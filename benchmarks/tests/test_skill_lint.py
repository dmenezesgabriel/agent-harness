"""Tests for SkillLintValidator (issue 037).

Covers UT-001 through UT-006 and IT-001.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from harness.skill_lint import LintError, LintResult, SkillLintValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_skill_dir(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp_path


# ---------------------------------------------------------------------------
# UT-001: clean skill dir passes (FR-006, AC-001)
# ---------------------------------------------------------------------------

def test_validate_clean_skill_dir_passes(tmp_path):
    _make_skill_dir(tmp_path, {
        "SKILL.md": "# Skill\n\nSee [rules](references/rules.md) and [template](assets/template.md).",
        "references/rules.md": "# Rules",
        "assets/template.md": "# Template",
    })
    result = SkillLintValidator().validate(tmp_path)
    assert result.passed
    assert result.errors == []


def test_validate_no_links_passes(tmp_path):
    _make_skill_dir(tmp_path, {"SKILL.md": "# Skill\n\nNo links here."})
    result = SkillLintValidator().validate(tmp_path)
    assert result.passed
    assert result.errors == []


# ---------------------------------------------------------------------------
# UT-002: missing SKILL.md → one LintError mentioning SKILL.md (FR-003, AC-002)
# ---------------------------------------------------------------------------

def test_validate_missing_skill_md_returns_one_error(tmp_path):
    result = SkillLintValidator().validate(tmp_path)
    assert not result.passed
    assert len(result.errors) == 1
    assert "SKILL.md" in result.errors[0].message


# ---------------------------------------------------------------------------
# UT-003: broken references/ link → one LintError naming the missing file (FR-004, AC-003)
# ---------------------------------------------------------------------------

def test_validate_broken_references_link(tmp_path):
    _make_skill_dir(tmp_path, {
        "SKILL.md": "See [rules](references/missing-file.md).",
    })
    result = SkillLintValidator().validate(tmp_path)
    assert not result.passed
    assert len(result.errors) == 1
    assert "references/missing-file.md" in result.errors[0].path


# ---------------------------------------------------------------------------
# UT-004: broken assets/ link → one LintError naming the missing file (FR-005)
# ---------------------------------------------------------------------------

def test_validate_broken_assets_link(tmp_path):
    _make_skill_dir(tmp_path, {
        "SKILL.md": "See [template](assets/missing-template.md).",
    })
    result = SkillLintValidator().validate(tmp_path)
    assert not result.passed
    assert len(result.errors) == 1
    assert "assets/missing-template.md" in result.errors[0].path


# ---------------------------------------------------------------------------
# UT-005: two broken links → exactly two LintError entries (FR-004, AC-004)
# ---------------------------------------------------------------------------

def test_validate_two_broken_links_returns_two_errors(tmp_path):
    _make_skill_dir(tmp_path, {
        "SKILL.md": "See [rules](references/missing.md) and [template](assets/missing.md).",
    })
    result = SkillLintValidator().validate(tmp_path)
    assert not result.passed
    assert len(result.errors) == 2


# ---------------------------------------------------------------------------
# UT-006: no forbidden imports (NFR-001, NFR-002)
# ---------------------------------------------------------------------------

def test_skill_lint_has_no_forbidden_imports():
    import harness.skill_lint as mod
    source = Path(mod.__file__).read_text()
    for forbidden in ("subprocess", "harness.adapters", "harness.evaluators", "harness.tracking"):
        assert forbidden not in source, f"skill_lint.py contains '{forbidden}'"


# ---------------------------------------------------------------------------
# LintResult properties
# ---------------------------------------------------------------------------

def test_lint_result_skill_name(tmp_path):
    skill_dir = tmp_path / "plan-it"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill")
    result = SkillLintValidator().validate(skill_dir)
    assert result.skill == "plan-it"


def test_lint_result_passed_false_when_errors_present(tmp_path):
    result = LintResult(skill="test", errors=[LintError(path="SKILL.md", message="not found")])
    assert not result.passed


# ---------------------------------------------------------------------------
# IT-001: run.py exits with code 1 on lint failure; adapter never called (FR-007, AC-005)
# ---------------------------------------------------------------------------

def test_run_exits_on_lint_failure(tmp_path):
    from click.testing import CliRunner
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from run import main

    skill_dir = tmp_path / "broken-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("See [rules](references/missing.md).")

    runner = CliRunner()
    with patch("run.run_experiment") as mock_experiment:
        result = runner.invoke(main, [
            "--skill", "plan-it",
            "--platform", "claude-code",
            "--skill-dir", str(skill_dir),
            "--dry-run",
        ])

    assert result.exit_code == 1
    assert "missing.md" in result.output
    mock_experiment.assert_not_called()
