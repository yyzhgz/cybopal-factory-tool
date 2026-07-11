from __future__ import annotations

import asyncio
from collections import deque
from typing import Any

from app.core.config import Settings
from app.domain import CommandResult
from app.ssh.base import InteractiveProcess


class AsyncSSHInteractiveProcess:
    def __init__(self, connection: Any, process: Any) -> None:
        self._connection = connection
        self._process = process
        self._output: deque[str] = deque(maxlen=240)
        self._stdout_task = asyncio.create_task(self._collect_output(process.stdout))
        self._stderr_task = asyncio.create_task(self._collect_output(process.stderr))

    async def write(self, data: str) -> None:
        self._process.stdin.write(data)
        await self._process.stdin.drain()

    async def terminate(self) -> None:
        self._stdout_task.cancel()
        self._stderr_task.cancel()
        try:
            self._process.stdin.write("\x03")
            await self._process.stdin.drain()
        except Exception:
            pass
        try:
            self._process.terminate()
        except Exception:
            pass
        self._connection.close()
        await self._connection.wait_closed()

    def recent_output(self) -> str:
        return "".join(self._output)[-12000:]

    async def _collect_output(self, stream: Any) -> None:
        try:
            async for chunk in stream:
                self._output.append(str(chunk))
        except asyncio.CancelledError:
            return
        except Exception as exc:
            self._output.append(f"\n[output capture stopped: {exc}]\n")


class AsyncSSHService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self, command: str, timeout: int = 60) -> CommandResult:
        import asyncssh

        async with asyncssh.connect(
            self._settings.device_host,
            username=self._settings.ssh_username,
            password=self._settings.ssh_password,
            known_hosts=None,
        ) as connection:
            result = await asyncio.wait_for(
                connection.run(command, check=False), timeout=timeout
            )
            return CommandResult(
                exit_status=result.exit_status,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
            )

    async def start_interactive(
        self, command: str, term_type: str = "xterm"
    ) -> InteractiveProcess:
        import asyncssh

        connection = await asyncssh.connect(
            self._settings.device_host,
            username=self._settings.ssh_username,
            password=self._settings.ssh_password,
            known_hosts=None,
        )
        process = await connection.create_process(
            command,
            term_type=term_type,
            term_size=(120, 40),
        )
        return AsyncSSHInteractiveProcess(connection, process)
