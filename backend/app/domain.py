from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OperationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class OperationLog:
    message: str
    level: OperationLevel = OperationLevel.INFO
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


@dataclass
class Diagnosis:
    current_status: str
    possible_cause: str
    suggested_action: str
    estimated_recovery_time: str
    recovery_action: Optional[str] = None


@dataclass
class OperationResult:
    success: bool
    status: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    diagnosis: Optional[Diagnosis] = None
    logs: List[OperationLog] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.diagnosis is None:
            payload["diagnosis"] = None
        return payload


@dataclass
class CommandResult:
    exit_status: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_status == 0


@dataclass
class ContainerInfo:
    container_id: str
    image: str
    name: str
    created_at: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

