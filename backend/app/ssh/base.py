from __future__ import annotations

from typing import Protocol

from app.domain import CommandResult


class InteractiveProcess(Protocol):
    async def write(self, data: str) -> None:
        ...

    async def terminate(self) -> None:
        ...

    def recent_output(self) -> str:
        ...


class SSHClient(Protocol):
    async def run(self, command: str, timeout: int = 60) -> CommandResult:
        ...

    async def start_interactive(
        self, command: str, term_type: str = "xterm"
    ) -> InteractiveProcess:
        ...
