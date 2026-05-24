"""Tests for WorkspaceManager ABC, TempWorkspaceManager, and FakeWorkspaceManager.

Covers UT-001 through UT-005 and IT-001 from issue 028.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.adapters.workspace import TempWorkspaceManager, WorkspaceManager
from harness.models import Task
from tests.fakes.fake_workspace_manager import FakeWorkspaceManager


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def task() -> Task:
    return Task(
        id="test-001",
        skill="plan-it",
        title="Test Task",
        instruction="Do something",
        evaluator="plan",
    )


@pytest.fixture
def fixture_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# UT-001: FakeWorkspaceManager.init_workspace returns fixture_path, no real dir
# ---------------------------------------------------------------------------

def test_fake_init_workspace_returns_fixture_path(task, fixture_dir):
    fake = FakeWorkspaceManager(fixture_path=fixture_dir)
    result = fake.init_workspace(task)
    assert result == fixture_dir


def test_fake_init_workspace_does_not_create_directory(task, tmp_path):
    nonexistent = tmp_path / "ghost"
    fake = FakeWorkspaceManager(fixture_path=nonexistent)
    result = fake.init_workspace(task)
    assert result == nonexistent
    assert not nonexistent.exists()


# ---------------------------------------------------------------------------
# UT-002: FakeWorkspaceManager.snapshot_workspace records path and returns data
# ---------------------------------------------------------------------------

def test_fake_snapshot_workspace_records_path_and_returns_data(tmp_path):
    snapshot_data = {"tasks/issues/001.md": "# issue"}
    fake = FakeWorkspaceManager(fixture_path=tmp_path, snapshot_data=snapshot_data)
    some_path = tmp_path / "run-1"

    returned = fake.snapshot_workspace(some_path)

    assert returned == snapshot_data
    assert some_path in fake.recorded_snapshots


def test_fake_snapshot_workspace_accumulates_multiple_calls(tmp_path):
    fake = FakeWorkspaceManager(fixture_path=tmp_path)
    paths = [tmp_path / f"run-{i}" for i in range(3)]
    for p in paths:
        fake.snapshot_workspace(p)
    assert fake.recorded_snapshots == paths


# ---------------------------------------------------------------------------
# UT-003: FakeWorkspaceManager.cleanup is a no-op
# ---------------------------------------------------------------------------

def test_fake_cleanup_does_not_raise(tmp_path):
    fake = FakeWorkspaceManager(fixture_path=tmp_path)
    fake.cleanup(tmp_path)  # must not raise


def test_fake_cleanup_does_not_remove_directory(tmp_path):
    fake = FakeWorkspaceManager(fixture_path=tmp_path)
    fake.cleanup(tmp_path)
    assert tmp_path.exists()


# ---------------------------------------------------------------------------
# UT-004: TempWorkspaceManager is an instance of WorkspaceManager
# ---------------------------------------------------------------------------

def test_temp_workspace_manager_isinstance_workspace_manager():
    assert isinstance(TempWorkspaceManager(), WorkspaceManager)


# ---------------------------------------------------------------------------
# UT-005: ClaudeCodeAdapter() default has workspace_manager = TempWorkspaceManager
# ---------------------------------------------------------------------------

def test_claude_code_adapter_default_workspace_manager():
    from harness.adapters.claude_code import ClaudeCodeAdapter

    with patch("shutil.which", return_value="/usr/bin/claude"):
        adapter = ClaudeCodeAdapter()

    assert isinstance(adapter.workspace_manager, TempWorkspaceManager)


# ---------------------------------------------------------------------------
# IT-001: Adapter delegates workspace lifecycle to FakeWorkspaceManager
# ---------------------------------------------------------------------------

def _stream_json_output() -> str:
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}}),
        json.dumps({"type": "result", "usage": {"input_tokens": 10, "output_tokens": 5}}),
    ]
    return "\n".join(lines)


def test_claude_code_adapter_delegates_workspace_lifecycle(task, fixture_dir):
    from harness.adapters.claude_code import ClaudeCodeAdapter

    fake = FakeWorkspaceManager(fixture_path=fixture_dir, snapshot_data={})
    cleanup_calls: list[Path] = []
    original_cleanup = fake.cleanup
    fake.cleanup = lambda p: cleanup_calls.append(p) or original_cleanup(p)  # type: ignore[method-assign]

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(
            stdout=_stream_json_output(),
            returncode=0,
        )
        adapter = ClaudeCodeAdapter(workspace_manager=fake)
        result = adapter.run(task)

    assert len(fake.recorded_snapshots) == 1
    assert fake.recorded_snapshots[0] == fixture_dir
    assert len(cleanup_calls) == 1
    assert result.error == ""


def test_claude_code_adapter_cleanup_called_on_timeout(task, fixture_dir):
    from harness.adapters.claude_code import ClaudeCodeAdapter
    import subprocess as sp

    fake = FakeWorkspaceManager(fixture_path=fixture_dir)
    cleanup_calls: list[Path] = []
    original_cleanup = fake.cleanup
    fake.cleanup = lambda p: cleanup_calls.append(p) or original_cleanup(p)  # type: ignore[method-assign]

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run", side_effect=sp.TimeoutExpired(cmd="claude", timeout=300)),
    ):
        adapter = ClaudeCodeAdapter(workspace_manager=fake)
        result = adapter.run(task)

    assert result.error == "timeout"
    assert len(cleanup_calls) == 1


# ---------------------------------------------------------------------------
# FR-004: FakeWorkspaceManager has no forbidden production imports
# ---------------------------------------------------------------------------

def test_fake_workspace_manager_has_no_production_imports():
    import importlib
    import harness.adapters.workspace as _mod
    source = Path(_mod.__file__).parent.parent.parent / "tests" / "fakes" / "fake_workspace_manager.py"
    text = source.read_text()
    for forbidden in ("subprocess", "tempfile", "git"):
        assert forbidden not in text, f"FakeWorkspaceManager imports '{forbidden}'"


# ---------------------------------------------------------------------------
# UT-001 (034): diff_workspace — new file only in "after" is returned
# ---------------------------------------------------------------------------

def test_diff_workspace_returns_only_new_file():
    from harness.adapters.workspace import diff_workspace

    before = {"skills/foo.md": "content", "opencode.json": "{}"}
    after = {
        "skills/foo.md": "content",
        "opencode.json": "{}",
        "docs/adrs/001.md": "# ADR",
    }
    result = diff_workspace(before, after)
    assert result == {"docs/adrs/001.md": "# ADR"}


def test_diff_workspace_empty_before_returns_all_after():
    from harness.adapters.workspace import diff_workspace

    after = {"tasks/issues/001.md": "# issue", "tasks/plan.md": "plan"}
    result = diff_workspace({}, after)
    assert result == after


# ---------------------------------------------------------------------------
# UT-002 (034): diff_workspace — modified file (same path, changed content) is included
# ---------------------------------------------------------------------------

def test_diff_workspace_includes_modified_file():
    from harness.adapters.workspace import diff_workspace

    before = {"README.md": "old content", "skills/bar.md": "unchanged"}
    after = {"README.md": "new content", "skills/bar.md": "unchanged"}
    result = diff_workspace(before, after)
    assert "README.md" in result
    assert result["README.md"] == "new content"
    assert "skills/bar.md" not in result


def test_diff_workspace_unchanged_file_excluded():
    from harness.adapters.workspace import diff_workspace

    before = {"opencode.json": "{}", "agent_output.md": "output"}
    after = {"opencode.json": "{}", "agent_output.md": "output"}
    result = diff_workspace(before, after)
    assert result == {}
