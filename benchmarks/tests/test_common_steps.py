"""Unit tests for content-matching step definitions in common_steps.py.

Covers UT-001 (step_content_matches_regex) and UT-002 (step_frontmatter_key_value).
"""
import types

import pytest

from features.steps.common_steps import (
    step_content_matches_regex,
    step_frontmatter_key_value,
)


def _ctx(tmp_path):
    return types.SimpleNamespace(ws=tmp_path)


# ── UT-001: step_content_matches_regex ───────────────────────────────────────


class TestStepContentMatchesRegex:
    def test_passes_when_regex_matches(self, tmp_path):
        (tmp_path / "issues").mkdir()
        (tmp_path / "issues" / "001-task.md").write_text(
            "FR-001: A signed-in user can create a project\n"
        )
        step_content_matches_regex(_ctx(tmp_path), "issues/*.md", r"FR-\d{3}:")

    def test_fails_with_filename_when_no_match(self, tmp_path):
        (tmp_path / "issues").mkdir()
        (tmp_path / "issues" / "001-task.md").write_text("Add project feature\n")
        with pytest.raises(AssertionError) as exc:
            step_content_matches_regex(_ctx(tmp_path), "issues/*.md", r"FR-\d{3}:")
        assert "001-task.md" in str(exc.value)

    def test_vacuous_pass_when_no_files(self, tmp_path):
        step_content_matches_regex(_ctx(tmp_path), "issues/*.md", r"FR-\d{3}:")

    def test_reports_only_non_matching_files(self, tmp_path):
        (tmp_path / "issues").mkdir()
        (tmp_path / "issues" / "001-good.md").write_text("FR-001: valid\n")
        (tmp_path / "issues" / "002-bad.md").write_text("No ID here\n")
        with pytest.raises(AssertionError) as exc:
            step_content_matches_regex(_ctx(tmp_path), "issues/*.md", r"FR-\d{3}:")
        assert "002-bad.md" in str(exc.value)
        assert "001-good.md" not in str(exc.value)


# ── UT-002: step_frontmatter_key_value ───────────────────────────────────────


def _fm_file(path, pairs, body="content"):
    lines = "\n".join(f"{k}: {v}" for k, v in pairs.items())
    path.write_text(f"---\n{lines}\n---\n\n{body}\n")


class TestStepFrontmatterKeyValue:
    def test_passes_for_active_status(self, tmp_path):
        (tmp_path / "issues").mkdir()
        _fm_file(tmp_path / "issues" / "001-task.md", {"status": "active"})
        step_frontmatter_key_value(_ctx(tmp_path), "issues/*.md", "status", "active")

    def test_fails_for_draft_status(self, tmp_path):
        (tmp_path / "issues").mkdir()
        _fm_file(tmp_path / "issues" / "001-task.md", {"status": "draft"})
        with pytest.raises(AssertionError) as exc:
            step_frontmatter_key_value(_ctx(tmp_path), "issues/*.md", "status", "active")
        assert "001-task.md" in str(exc.value)

    def test_fails_when_key_absent(self, tmp_path):
        (tmp_path / "issues").mkdir()
        _fm_file(tmp_path / "issues" / "001-task.md", {"title": "my task"})
        with pytest.raises(AssertionError) as exc:
            step_frontmatter_key_value(_ctx(tmp_path), "issues/*.md", "status", "active")
        assert "001-task.md" in str(exc.value)

    def test_vacuous_pass_when_no_files(self, tmp_path):
        step_frontmatter_key_value(_ctx(tmp_path), "issues/*.md", "status", "active")

    def test_tolerates_no_space_after_colon(self, tmp_path):
        (tmp_path / "issues").mkdir()
        (tmp_path / "issues" / "001-task.md").write_text("---\nstatus:active\n---\ncontent\n")
        step_frontmatter_key_value(_ctx(tmp_path), "issues/*.md", "status", "active")
