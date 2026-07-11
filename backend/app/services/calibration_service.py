from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import Optional

from app.commands.calibration_commands import (
    CONTROL_KEY_MAP,
    calibration_file_state_command,
    docker_ps_command,
    install_dependencies_command,
    patch_config_command,
    prepare_motion_services_command,
    restart_container_command,
    select_latest_container,
    start_keyboard_control_command,
)
from app.core.config import Settings
from app.domain import (
    CommandResult,
    ContainerInfo,
    Diagnosis,
    OperationLevel,
    OperationLog,
    OperationResult,
)
from app.services.calibration_state import (
    CalibrationStateEvaluator,
    CalibrationToolState,
    TerminalMessage,
    TerminalMessageParser,
)
from app.services.log_service import LogService
from app.ssh.base import InteractiveProcess, SSHClient


@dataclass
class _StepFailure(Exception):
    label: str
    result: CommandResult


class CalibrationService:
    def __init__(
        self,
        settings: Settings,
        ssh_client: SSHClient,
        log_service: LogService,
    ) -> None:
        self._settings = settings
        self._ssh = ssh_client
        self._logs = log_service
        self._container: Optional[ContainerInfo] = None
        self._session: Optional[InteractiveProcess] = None
        self._first_calibration: Optional[bool] = None
        self._last_start_command: Optional[str] = None
        self._parser = TerminalMessageParser()
        self._evaluator = CalibrationStateEvaluator()

    async def connect_device(self) -> OperationResult:
        self._logs.clear()
        self._logs.info(f"Connecting to device {self._settings.device_host}...")
        try:
            container = await self._select_container()
        except _StepFailure as exc:
            return self._failed(
                "connect_failed",
                "设备连接失败",
                exc,
                "无法通过 SSH 读取 Docker 容器列表。",
                "设备未开机、网线未连接、SSH 密码不正确，或 Docker 服务未运行。",
                "确认设备电源和 USB/RNDIS 网络后，再点击重新连接。",
                "约 30 秒",
            )

        self._logs.success("Device connected.")
        return self._ok(
            "connected",
            "设备已连接",
            data={
                "host": self._settings.device_host,
                "container": container.to_dict(),
            },
        )

    async def prepare_environment(self) -> OperationResult:
        try:
            container = await self._ensure_container()
            await self._run_step(
                "Installing calibration dependencies",
                install_dependencies_command(
                    container.container_id, self._settings.ssh_password
                ),
                timeout=240,
            )
            await self._run_step(
                "Updating calibration config",
                patch_config_command(
                    container.container_id,
                    self._settings.calibration_config_path,
                    self._settings.ssh_password,
                ),
                timeout=60,
            )
            await self._run_step(
                "Preparing motion service",
                prepare_motion_services_command(
                    container.container_id, self._settings.ssh_password
                ),
                timeout=80,
            )
            self._first_calibration = await self._detect_first_calibration(container)
        except _StepFailure as exc:
            return self._failed(
                "prepare_failed",
                "准备标定环境失败",
                exc,
                "标定环境没有准备完成。",
                "依赖安装失败、配置文件路径不存在，或 motion 服务没有正常重启。",
                "点击重新准备；如果仍失败，请检查设备是否进入最新容器。",
                "约 1 分钟",
            )

        mode = "first_calibration" if self._first_calibration else "adjust_calibration"
        message = "准备完成：首次标定模式" if self._first_calibration else "准备完成：修正标定模式"
        return self._ok(
            "prepared",
            message,
            data={
                "container": container.to_dict(),
                "mode": mode,
                "firstCalibration": self._first_calibration,
            },
        )

    async def start_calibration_tool(self) -> OperationResult:
        try:
            container = await self._ensure_container()
            if self._first_calibration is None:
                self._first_calibration = await self._detect_first_calibration(container)
            command = start_keyboard_control_command(
                container.container_id,
                self._first_calibration,
                self._settings.ssh_password,
            )
            await self._start_keyboard_session(command)
        except _StepFailure as exc:
            return self._failed(
                "start_failed",
                "标定工具启动失败",
                exc,
                "标定工具没有启动。",
                "首次标定判断失败，或容器内 cytobot_keyboard_control 无法运行。",
                "重新准备环境后再启动；如果提示缺少依赖，请重新执行准备环境。",
                "约 30 秒",
            )
        except Exception as exc:
            self._logs.error(f"Calibration tool start failed: {exc}")
            return OperationResult(
                success=False,
                status="start_failed",
                message="标定工具启动失败",
                diagnosis=Diagnosis(
                    current_status="无法创建交互式标定会话。",
                    possible_cause="SSH 交互终端不可用，或设备拒绝启动标定工具。",
                    suggested_action="重新连接设备并再次启动标定工具。",
                    estimated_recovery_time="约 30 秒",
                    recovery_action="connect",
                ),
                logs=self._logs.recent(),
            )

        state = self._tool_state()
        return self._ok(
            "tool_started",
            "标定工具已启动",
            data=self._tool_data(state),
        )

    async def send_control(self, action: str) -> OperationResult:
        if self._session is None:
            return OperationResult(
                success=False,
                status="tool_not_started",
                message="请先启动标定工具",
                diagnosis=Diagnosis(
                    current_status="当前没有可用的标定控制会话。",
                    possible_cause="还没有启动标定工具，或容器已被重启。",
                    suggested_action="点击“启动标定工具”，再进行关节控制。",
                    estimated_recovery_time="约 10 秒",
                    recovery_action="start_tool",
                ),
                logs=self._logs.recent(),
            )

        payload = CONTROL_KEY_MAP.get(action)
        if payload is None:
            return OperationResult(
                success=False,
                status="unsupported_control",
                message="暂不支持这个控制动作",
                logs=self._logs.recent(),
            )

        state = self._tool_state()
        if not state.can_control and action not in {"toggle_joint_limits", "recover", "interrupt"}:
            return OperationResult(
                success=False,
                status="tool_not_ready",
                message="标定工具暂不可用，控制按钮已锁定",
                data=self._tool_data(state),
                diagnosis=Diagnosis(
                    current_status=state.reason,
                    possible_cause="当前 Message 状态不允许继续标定。",
                    suggested_action="点击“尝试恢复”，或点击“重新启动标定服务”。",
                    estimated_recovery_time="约 10-30 秒",
                    recovery_action="try_recover",
                ),
                logs=self._logs.recent(),
            )

        await self._session.write(payload)
        await asyncio.sleep(0.15)
        self._logs.append(f"Control sent: {action}", OperationLevel.SUCCESS)
        state = self._tool_state()
        return self._ok(
            "control_sent",
            "控制指令已发送",
            data={"action": action, **self._tool_data(state)},
        )

    async def try_recover_tool(self) -> OperationResult:
        if self._session is None:
            return OperationResult(
                success=False,
                status="tool_not_started",
                message="请先启动标定工具",
                data=self._tool_data(self._tool_state()),
                logs=self._logs.recent(),
            )

        self._logs.warning("Trying calibration recovery...")
        await self._session.write(CONTROL_KEY_MAP["toggle_joint_limits"])
        await asyncio.sleep(0.2)
        await self._session.write(CONTROL_KEY_MAP["recover"])
        await asyncio.sleep(0.5)
        state = self._tool_state()
        return self._ok(
            "recover_sent",
            "已尝试恢复标定工具" if state.can_control else "已尝试恢复，标定工具仍不可用",
            data=self._tool_data(state),
        )

    async def restart_calibration_tool(self) -> OperationResult:
        if self._session is not None:
            self._logs.warning("Stopping calibration control tool...")
            await self._session.terminate()
            self._session = None
        if self._last_start_command is None:
            return await self.start_calibration_tool()

        await self._start_keyboard_session(self._last_start_command)
        state = self._tool_state()
        return self._ok(
            "tool_restarted",
            "标定服务已重新启动",
            data=self._tool_data(state),
        )

    def tool_status(self) -> OperationResult:
        state = self._tool_state()
        return self._ok(
            "tool_status",
            "标定工具可用" if state.can_control else "标定工具暂不可用",
            data=self._tool_data(state),
        )

    async def finish_calibration(self) -> OperationResult:
        try:
            container = await self._ensure_container()
            await self._run_step(
                "Restarting Docker container",
                restart_container_command(container.container_id, self._settings.ssh_password),
                timeout=120,
            )
            if self._session is not None:
                await self._session.terminate()
                self._session = None
        except _StepFailure as exc:
            return self._failed(
                "finish_failed",
                "容器重启失败",
                exc,
                "标定完成后的容器重启没有成功。",
                "Docker 服务异常，或当前容器 ID 已变化。",
                "重新连接设备后再次点击完成标定。",
                "约 30 秒",
            )

        return self._ok(
            "finished",
            "标定已完成，容器已重启",
            data={"container": self._container.to_dict() if self._container else None},
        )

    async def stop_tool(self) -> OperationResult:
        if self._session is not None:
            await self._session.terminate()
            self._session = None
            self._logs.warning("Calibration tool stopped.")
        return self._ok("tool_stopped", "标定工具已停止")

    def logs(self) -> list[OperationLog]:
        return self._logs.recent()

    async def _ensure_container(self) -> ContainerInfo:
        if self._container is not None:
            return self._container
        return await self._select_container()

    async def _select_container(self) -> ContainerInfo:
        result = await self._run_step(
            "Finding latest Docker container",
            docker_ps_command(self._settings.ssh_password),
            timeout=40,
        )
        container = select_latest_container(result.stdout, self._settings.container_hint)
        if container is None:
            raise _StepFailure("Finding latest Docker container", result)
        self._container = container
        self._logs.success(f"Selected container {container.name}.")
        return container

    async def _detect_first_calibration(self, container: ContainerInfo) -> bool:
        result = await self._run_step(
            "Checking calibration state",
            calibration_file_state_command(
                container.container_id,
                self._settings.calibration_flag_path,
                self._settings.ssh_password,
            ),
            timeout=30,
        )
        first = "first_calibration" in result.stdout
        if first:
            self._logs.warning("No calibration.yaml found. First calibration mode enabled.")
        else:
            self._logs.success("Existing calibration.yaml found. Normal mode enabled.")
        return first

    async def _run_step(
        self, label: str, command: str, timeout: int = 60
    ) -> CommandResult:
        self._logs.info(f"{label}...")
        result = await self._ssh.run(command, timeout=timeout)
        if not result.ok:
            detail = result.stderr.strip() or result.stdout.strip() or "no output"
            self._logs.error(f"{label} failed: {detail}")
            raise _StepFailure(label, result)
        self._logs.success(f"{label} OK.")
        return result

    async def _start_keyboard_session(self, command: str) -> None:
        self._last_start_command = command
        self._logs.info("Starting calibration control tool...")
        self._session = await self._ssh.start_interactive(command)
        await self._session.write(f"{self._settings.ssh_password}\n")
        entered = await self._wait_for_keyboard_screen(timeout_seconds=18)
        if not entered:
            self._logs.warning("Calibration tool has not shown keyboard screen yet.")
            return
        await self._session.write(CONTROL_KEY_MAP["toggle_joint_limits"])
        self._logs.success("Keyboard screen detected. Joint limits toggled.")
        await asyncio.sleep(0.5)

    async def _wait_for_keyboard_screen(self, timeout_seconds: float) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            if _looks_like_keyboard_screen(self._terminal_output()):
                return True
            await asyncio.sleep(0.25)
        return _looks_like_keyboard_screen(self._terminal_output())

    def _terminal_message(self) -> TerminalMessage:
        return self._parser.parse_latest(self._terminal_output())

    def _tool_state(self) -> CalibrationToolState:
        return self._evaluator.evaluate(
            self._terminal_message(),
            started=self._session is not None,
        )
    def _tool_data(self, state: CalibrationToolState) -> dict:
        return {
            "readiness": state.readiness,
            "ready": state.can_control,
            "canControl": state.can_control,
            "canSave": state.can_save,
            "messageLevel": state.message_level,
            "toolMessage": state.message_text,
            "stateReason": state.reason,
            "recoveryActions": state.recovery_actions,
            "started": self._session is not None,
            "firstCalibration": self._first_calibration,
            "terminalOutput": self._terminal_output(),
        }

    def _terminal_output(self) -> str:
        if self._session is None:
            return ""
        return self._session.recent_output()

    def _ok(self, status: str, message: str, data: Optional[dict] = None) -> OperationResult:
        return OperationResult(
            success=True,
            status=status,
            message=message,
            data=data or {},
            logs=self._logs.recent(),
        )

    def _failed(
        self,
        status: str,
        message: str,
        failure: _StepFailure,
        current_status: str,
        possible_cause: str,
        suggested_action: str,
        estimated_recovery_time: str,
    ) -> OperationResult:
        return OperationResult(
            success=False,
            status=status,
            message=message,
            diagnosis=Diagnosis(
                current_status=current_status,
                possible_cause=f"{possible_cause} 失败步骤：{failure.label}。",
                suggested_action=suggested_action,
                estimated_recovery_time=estimated_recovery_time,
                recovery_action="prepare",
            ),
            logs=self._logs.recent(),
        )


def _looks_like_keyboard_screen(output: str) -> bool:
    markers = (
        "CYTOBOT KEYBOARD CONTROL",
        "Control Instructions",
        "Joint Command Positions",
        "Message:",
        "Message[INFO]",
        "Message[ERROR]",
    )
    return any(marker in output for marker in markers)
