from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

CalibrationReadiness = Literal["ready", "not_ready"]
MessageLevel = Literal["INFO", "ERROR", "UNKNOWN"]


@dataclass(frozen=True)
class TerminalMessage:
    level: MessageLevel
    text: str
    raw: str


@dataclass(frozen=True)
class CalibrationToolState:
    readiness: CalibrationReadiness
    can_control: bool
    can_save: bool
    message_level: MessageLevel
    message_text: str
    reason: str
    recovery_actions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class TerminalMessageParser:
    _BRACKET_PATTERN = re.compile(r"Message\s*\[(INFO|ERROR)\]\s*:?\s*([^\r\n]*)")
    _COLON_PATTERN = re.compile(r"Message\s*:\s*([^\r\n]+)")

    def parse_latest(self, output: str) -> TerminalMessage:
        candidates: list[tuple[int, TerminalMessage]] = []

        for match in self._BRACKET_PATTERN.finditer(output):
            level = match.group(1)
            text = match.group(2).strip()
            candidates.append(
                (
                    match.start(),
                    TerminalMessage(level=level, text=text, raw=match.group(0).strip()),
                )
            )

        for match in self._COLON_PATTERN.finditer(output):
            text = match.group(1).strip()
            level: MessageLevel = "ERROR" if text.upper().startswith("ERROR") else "INFO"
            candidates.append(
                (
                    match.start(),
                    TerminalMessage(level=level, text=text, raw=match.group(0).strip()),
                )
            )

        if not candidates:
            return TerminalMessage(level="UNKNOWN", text="", raw="")

        _, message = max(candidates, key=lambda item: item[0])
        return message


class CalibrationStateEvaluator:
    def evaluate(self, message: TerminalMessage, started: bool) -> CalibrationToolState:
        if not started:
            return CalibrationToolState(
                readiness="not_ready",
                can_control=False,
                can_save=False,
                message_level=message.level,
                message_text=message.text,
                reason="标定工具尚未启动。",
                recovery_actions=["start_tool"],
            )

        if message.level == "UNKNOWN":
            return CalibrationToolState(
                readiness="not_ready",
                can_control=False,
                can_save=False,
                message_level=message.level,
                message_text=message.text,
                reason="标定工具正在启动，尚未进入键盘控制界面。",
                recovery_actions=["restart_tool"],
            )

        if message.level == "ERROR":
            return CalibrationToolState(
                readiness="not_ready",
                can_control=False,
                can_save=False,
                message_level=message.level,
                message_text=message.text or "ERROR",
                reason="检测到 Message[ERROR]，标定工具暂不可用。",
                recovery_actions=["try_recover", "restart_tool"],
            )

        return CalibrationToolState(
            readiness="ready",
            can_control=True,
            can_save=True,
            message_level=message.level,
            message_text=message.text,
            reason="标定工具可用。",
            recovery_actions=[],
        )
