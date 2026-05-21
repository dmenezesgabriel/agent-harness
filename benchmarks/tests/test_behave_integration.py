"""Integration tests: behave runner against fixture workspaces.

IT-001: All new plan-it content-quality scenarios pass against a known-good fixture.
IT-002: FR scenario fails and names the offending file when FR IDs are missing.

Covers FR-003, FR-004, FR-005, FR-006, AC-002, NB-002 (Gherkin regex passthrough).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

BENCHMARKS_DIR = Path(__file__).parent.parent
FEATURES_DIR = BENCHMARKS_DIR / "features"

_GOOD_ISSUE = """\
---
status: active
---

## Requirements

FR-001: A signed-in user can create a project.

## Acceptance Criteria

Given a signed-in user, When they submit the create-project form, Then a project is created.

## Dependencies

None.

AFK

Covers FR-001
"""


def _behave(workspace: Path, feature: str, name_pattern: str | None = None) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable, "-m", "behave",
        "--no-capture",
        "--define", f"workspace={workspace}",
        str(FEATURES_DIR / feature),
    ]
    if name_pattern:
        cmd += ["--name", name_pattern]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=BENCHMARKS_DIR)


def _good_workspace(ws: Path, n: int = 2) -> None:
    """Scaffold a workspace that satisfies every plan-it.feature scenario."""
    issues = ws / "issues"
    issues.mkdir(parents=True)
    for i in range(1, n + 1):
        (issues / f"{i:03d}-task.md").write_text(_GOOD_ISSUE)
    (ws / "issues-lock.json").write_text(json.dumps({"next_id": n + 1}))


class TestPlanItBehaveIntegration:
    def test_good_fixture_all_scenarios_pass(self, tmp_path):
        """IT-001: full plan-it.feature passes against a well-formed fixture."""
        _good_workspace(tmp_path)
        result = _behave(tmp_path, "plan-it.feature")
        assert result.returncode == 0, (
            f"behave exited {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_fr_scenario_fails_on_missing_fr_id(self, tmp_path):
        """IT-002: FR scenario fails and names the bad file. Covers AC-002, NB-002."""
        issues = tmp_path / "issues"
        issues.mkdir()
        (issues / "001-bad.md").write_text("Add project feature\n")
        result = _behave(
            tmp_path,
            "plan-it.feature",
            name_pattern="functional requirement",
        )
        assert result.returncode != 0, "Expected behave to fail but it passed"
        assert "001-bad.md" in result.stdout + result.stderr
