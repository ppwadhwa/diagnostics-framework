from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class DiagnosticStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DiagnosticResult:
    test_name: str
    status: DiagnosticStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemInfo:
    name: str
    description: str = ""
    version: str = "0.1.0"


@dataclass
class TestInfo:
    name: str
    description: str
    fn: Callable


@dataclass
class PlotInfo:
    name: str
    description: str
    fn: Callable


@dataclass
class ReportInfo:
    name: str
    description: str
    fn: Callable


@dataclass
class DiagnosticSummary:
    system_name: str
    results: list[DiagnosticResult]
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.status == DiagnosticStatus.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.status == DiagnosticStatus.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == DiagnosticStatus.WARNING)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == DiagnosticStatus.ERROR)
