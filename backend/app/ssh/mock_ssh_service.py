from __future__ import annotations

import os
import time

from app.domain import CommandResult
from app.ssh.base import InteractiveProcess


class MockInteractiveProcess:
    def __init__(self) -> None:
        self.writes: list[str] = []
        self.closed = False
        self._state = os.getenv("CYBOPAL_MOCK_MESSAGE_STATE", "ready").strip().lower()
        self._started_at = time.monotonic()
        self._error_after_seconds = float(
            os.getenv("CYBOPAL_MOCK_ERROR_AFTER_SECONDS", "6")
        )
        self._transitioned_to_error = False
        self._output = self._initial_output()

    async def write(self, data: str) -> None:
        self.writes.append(data)
        if data == "R":
            self._state = "ready"
            self._transitioned_to_error = True
            self._output += "\nMessage[INFO]: recovered\n"
        elif data == "M":
            if self._is_error_state():
                self._output += "\nMessage[ERROR]: controller not ready\n"
            else:
                self._output += "\nMessage[INFO]: joint limits toggled\n"
        elif data == "\x03":
            self._output += "\nMessage[INFO]: interrupted\n"

    async def terminate(self) -> None:
        self.closed = True

    def recent_output(self) -> str:
        self._maybe_transition_to_error()
        return self._output

    def _initial_output(self) -> str:
        if self._state == "error":
            return (
                "CYTOBOT KEYBOARD CONTROL\n"
                "Speed Level: 2/7\n"
                "Mode: Stop\n"
                "Message[ERROR]: controller not ready\n"
            )
        return (
            "CYTOBOT KEYBOARD CONTROL\n"
            "Speed Level: 2/7\n"
            "Mode: Stop\n"
            "Message[INFO]: Ready\n"
        )

    def _is_error_state(self) -> bool:
        self._maybe_transition_to_error()
        return self._state == "error"

    def _maybe_transition_to_error(self) -> None:
        if self._state != "ready_then_error" or self._transitioned_to_error:
            return
        if time.monotonic() - self._started_at < self._error_after_seconds:
            return
        self._state = "error"
        self._transitioned_to_error = True
        self._output += "\nMessage[ERROR]: simulated message changed while monitoring\n"


class MockSSHService:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.interactive_commands: list[str] = []
        self.interactive = MockInteractiveProcess()

    async def run(self, command: str, timeout: int = 60) -> CommandResult:
        self.commands.append(command)
        if "docker ps -a" in command:
            return CommandResult(
                0,
                "c58fc20197b4|repo/daily-20260707-48ade6e7|"
                "cybopal_container-daily-20260707-48ade6e7|2026-07-07\n",
            )
        if "first_calibration" in command:
            return CommandResult(0, "first_calibration\n")
        if "docker restart" in command:
            return CommandResult(0, "c58fc20197b4\n")
        return CommandResult(0, "ok\n")

    async def start_interactive(
        self, command: str, term_type: str = "xterm"
    ) -> InteractiveProcess:
        self.interactive_commands.append(command)
        return self.interactive
