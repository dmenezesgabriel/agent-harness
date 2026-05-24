from __future__ import annotations

from pathlib import Path

from harness.adapters.workspace import WorkspaceManager
from harness.models import Task


class FakeWorkspaceManager(WorkspaceManager):
    def __init__(
        self,
        fixture_path: Path,
        snapshot_data: dict[str, str] | None = None,
    ) -> None:
        self.fixture_path = fixture_path
        self.snapshot_data: dict[str, str] = snapshot_data if snapshot_data is not None else {}
        self.recorded_snapshots: list[Path] = []

    def init_workspace(self, task: Task) -> Path:
        return self.fixture_path

    def snapshot_workspace(self, path: Path) -> dict[str, str]:
        self.recorded_snapshots.append(path)
        return self.snapshot_data

    def cleanup(self, path: Path) -> None:
        pass
