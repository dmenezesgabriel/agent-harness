"""Tests for OpenCodeAdapter token accumulation.

Covers UT-001, UT-002, and IT-001 from task 032.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.adapters.opencode import OpenCodeAdapter
from harness.adapters.workspace import WorkspaceManager
from harness.models import Task


@pytest.fixture
def task():
    return Task(
        id="t-001",
        skill="implement-it",
        title="Test task",
        instruction="Do something",
        evaluator="code",
    )


@pytest.fixture
def adapter():
    with patch("shutil.which", return_value="/usr/bin/opencode"):
        yield OpenCodeAdapter()


# ---------------------------------------------------------------------------
# UT-001: multi-step NDJSON accumulates token counts across all steps
# ---------------------------------------------------------------------------

def test_accumulates_tokens_across_steps(adapter, task):
    ndjson = (
        '{"type":"step_finish","part":{"tokens":{"input":100,"output":20}}}\n'
        '{"type":"text","part":{"text":"hello"}}\n'
        '{"type":"step_finish","part":{"tokens":{"input":200,"output":30}}}\n'
        '{"type":"step_finish","part":{"tokens":{"input":50,"output":10}}}\n'
    )
    result = adapter._parse_output(ndjson, task, 100.0)
    assert result.input_tokens == 350  # 100 + 200 + 50
    assert result.output_tokens == 60   # 20 + 30 + 10


# ---------------------------------------------------------------------------
# UT-002: no step_finish events → zero tokens, no crash
# ---------------------------------------------------------------------------

def test_no_step_finish_events_returns_zero_tokens(adapter, task):
    ndjson = (
        '{"type":"text","part":{"text":"hello"}}\n'
        '{"type":"text","part":{"text":"world"}}\n'
    )
    result = adapter._parse_output(ndjson, task, 100.0)
    assert result.input_tokens == 0
    assert result.output_tokens == 0


def test_empty_output_returns_zero_tokens(adapter, task):
    result = adapter._parse_output("", task, 100.0)
    assert result.input_tokens == 0
    assert result.output_tokens == 0


# ---------------------------------------------------------------------------
# IT-001: full run() path with mocked subprocess — token counts exceed any
#         single step's count (covers AC-001 end-to-end without live CLI)
# ---------------------------------------------------------------------------

class _StubWorkspaceManager(WorkspaceManager):
    """Returns a real temp dir; records calls for assertion."""

    def __init__(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmpdir.name)

    def init_workspace(self, task):
        return self._dir

    def snapshot_workspace(self, path):
        return {}

    def cleanup(self, path):
        self._tmpdir.cleanup()


_MULTISTEP_NDJSON = (
    '{"type":"step_finish","part":{"tokens":{"input":100,"output":20}}}\n'
    '{"type":"text","part":{"text":"step one done"}}\n'
    '{"type":"step_finish","part":{"tokens":{"input":200,"output":30}}}\n'
    '{"type":"step_finish","part":{"tokens":{"input":50,"output":10}}}\n'
)


def test_run_accumulates_tokens_across_steps(task):
    """IT-001 (032): run() reports totals greater than any individual step."""
    stub_ws = _StubWorkspaceManager()
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    mock_result.stdout = _MULTISTEP_NDJSON

    with (
        patch("shutil.which", return_value="/usr/bin/opencode"),
        patch("subprocess.run", return_value=mock_result),
        patch("shutil.copy2"),
        patch("shutil.copytree"),
    ):
        adapter = OpenCodeAdapter(workspace_manager=stub_ws)
        result = adapter.run(task)

    # Totals: input 100+200+50=350, output 20+30+10=60
    # Max single step: input=200, output=30
    assert result.input_tokens == 350
    assert result.output_tokens == 60
    assert result.input_tokens > 200   # greater than any single step
    assert result.output_tokens > 30   # greater than any single step


# ---------------------------------------------------------------------------
# IT-001 (034): WITH_SKILL snapshot excludes scaffolding files
# ---------------------------------------------------------------------------

class _SnapshotSequenceWorkspaceManager(WorkspaceManager):
    """Returns successive snapshots per call; simulates before/after state."""

    def __init__(self, snapshots: list[dict[str, str]]) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmpdir.name)
        self._snapshots = iter(snapshots)

    def init_workspace(self, task) -> Path:
        return self._dir

    def snapshot_workspace(self, path) -> dict[str, str]:
        return next(self._snapshots)

    def cleanup(self, path) -> None:
        self._tmpdir.cleanup()


_SCAFFOLD_FILES = {
    "skills/plan-it/SKILL.md": "# plan-it skill",
    "opencode.json": '{"skills":{"paths":["skills"]}}',
}

_AFTER_FILES = {
    **_SCAFFOLD_FILES,
    "docs/adrs/001.md": "# ADR 001",
    "tasks/issues/001.md": "# Task 001",
}


def test_snapshot_excludes_scaffold_files(task):
    """IT-001 (034): snapshot contains only agent-created files, not skills/ or opencode.json."""
    stub_ws = _SnapshotSequenceWorkspaceManager(
        snapshots=[_SCAFFOLD_FILES, _AFTER_FILES]
    )
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    mock_result.stdout = '{"type":"text","part":{"text":"done"}}'

    with (
        patch("shutil.which", return_value="/usr/bin/opencode"),
        patch("subprocess.run", return_value=mock_result),
        patch("shutil.copy2"),
        patch("shutil.copytree"),
    ):
        adapter = OpenCodeAdapter(workspace_manager=stub_ws)
        result = adapter.run(task)

    assert "skills/plan-it/SKILL.md" not in result.workspace_snapshot
    assert "opencode.json" not in result.workspace_snapshot
    assert "docs/adrs/001.md" in result.workspace_snapshot
    assert "tasks/issues/001.md" in result.workspace_snapshot
    assert result.evaluator_details.get("scaffold_files_filtered") == 2


def test_snapshot_contains_all_agent_files_when_no_scaffold(task):
    """AC-002 (034): snapshot returns all agent-written files when scaffold is already excluded."""
    agent_files = {
        "tasks/issues/001.md": "# Task 001",
        "docs/adrs/001.md": "# ADR",
    }
    # First snapshot (before) has no scaffold, second (after) has only agent files
    stub_ws = _SnapshotSequenceWorkspaceManager(snapshots=[{}, agent_files])
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    mock_result.stdout = '{"type":"text","part":{"text":"done"}}'

    with (
        patch("shutil.which", return_value="/usr/bin/opencode"),
        patch("subprocess.run", return_value=mock_result),
        patch("shutil.copy2"),
        patch("shutil.copytree"),
    ):
        adapter = OpenCodeAdapter(workspace_manager=stub_ws)
        result = adapter.run(task)

    assert result.workspace_snapshot == agent_files
    assert "scaffold_files_filtered" not in result.evaluator_details
