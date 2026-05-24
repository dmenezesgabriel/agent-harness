from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from harness.models import Finding, RunSummary, Task, TaskResult


class Tracker(ABC):
    @abstractmethod
    def log_result(
        self,
        result: TaskResult,
        task: Task,
        skill_dir: str | None = None,
        skill_content_hash: str | None = None,
    ) -> str: ...

    @abstractmethod
    def log_summary(
        self,
        summary: RunSummary,
        skill_content_hash: str | None = None,
        skill_snapshot_dir: Path | None = None,
    ) -> None: ...

    @abstractmethod
    def log_finding(self, finding: Finding) -> None: ...
