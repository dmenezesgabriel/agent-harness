from __future__ import annotations

import sys
from pathlib import Path

from harness.models import Finding, RunSummary, Task, TaskResult
from harness.tracking.base import Tracker


class NullTracker(Tracker):
    def __init__(self) -> None:
        print("[tracker] dry-run mode: experiment tracking is disabled", file=sys.stderr)

    def log_result(
        self,
        result: TaskResult,
        task: Task,
        skill_dir: str | None = None,
        skill_content_hash: str | None = None,
    ) -> str:
        return ""

    def log_summary(
        self,
        summary: RunSummary,
        skill_content_hash: str | None = None,
        skill_snapshot_dir: Path | None = None,
    ) -> None:
        pass

    def log_finding(self, finding: Finding) -> None:
        pass
