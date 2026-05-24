from __future__ import annotations

import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from harness.adapters._workspace import diff_workspace
from harness.adapters._workspace import init_workspace as _init_workspace
from harness.adapters._workspace import snapshot_workspace as _snapshot_workspace
from harness.models import Task

__all__ = ["WorkspaceManager", "TempWorkspaceManager", "diff_workspace"]


class WorkspaceManager(ABC):
    @abstractmethod
    def init_workspace(self, task: Task) -> Path: ...

    @abstractmethod
    def snapshot_workspace(self, path: Path) -> dict[str, str]: ...

    @abstractmethod
    def cleanup(self, path: Path) -> None: ...


class TempWorkspaceManager(WorkspaceManager):
    def init_workspace(self, task: Task) -> Path:
        tmp = tempfile.mkdtemp()
        workspace = Path(tmp)
        _init_workspace(workspace)
        return workspace

    def snapshot_workspace(self, path: Path) -> dict[str, str]:
        return _snapshot_workspace(path)

    def cleanup(self, path: Path) -> None:
        shutil.rmtree(path, ignore_errors=True)
