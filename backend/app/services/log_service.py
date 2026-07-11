from __future__ import annotations

from threading import Lock
from typing import List

from app.domain import OperationLevel, OperationLog


class LogService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._logs: List[OperationLog] = []

    def append(self, message: str, level: OperationLevel = OperationLevel.INFO) -> None:
        with self._lock:
            self._logs.append(OperationLog(message=message, level=level))
            self._logs = self._logs[-300:]

    def info(self, message: str) -> None:
        self.append(message, OperationLevel.INFO)

    def success(self, message: str) -> None:
        self.append(message, OperationLevel.SUCCESS)

    def warning(self, message: str) -> None:
        self.append(message, OperationLevel.WARNING)

    def error(self, message: str) -> None:
        self.append(message, OperationLevel.ERROR)

    def recent(self) -> List[OperationLog]:
        with self._lock:
            return list(self._logs)

    def clear(self) -> None:
        with self._lock:
            self._logs.clear()

