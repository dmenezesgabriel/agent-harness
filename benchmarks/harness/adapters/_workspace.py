"""Shared workspace utilities for benchmark adapters.

Each adapter creates its own isolated temp directory (via
``with tempfile.TemporaryDirectory() as tmp:``) and then calls
``init_workspace`` to turn it into a proper git root with pre-created
output subdirectories.  After the agent exits, ``snapshot_workspace``
captures every file the agent wrote.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def init_workspace(workspace: Path) -> None:
    """Initialize an isolated git workspace: git init + pre-create output dirs."""
    subprocess.run(
        ["git", "init", "-q", "--initial-branch=main", str(workspace)],
        check=True,
        capture_output=True,
    )
    for d in ["issues", "docs/adrs", "implementation"]:
        (workspace / d).mkdir(parents=True, exist_ok=True)


def snapshot_workspace(workspace: Path) -> dict[str, str]:
    """Capture every file the agent wrote, keyed by relative path.

    Skips the seeded ``scripts/`` directory and the ``.git`` internals.
    """
    snapshot: dict[str, str] = {}
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(workspace)
        if rel.parts[0] in ("scripts", ".git"):
            continue
        try:
            snapshot[str(rel)] = p.read_text(errors="replace")
        except OSError:
            pass
    return snapshot
