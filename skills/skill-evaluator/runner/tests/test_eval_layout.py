from pathlib import Path

from runner.eval_layout import fixture_input_files, has_ignored_part


class TestHasIgnoredPart:
    def test_flags_vcs_and_build_dirs(self) -> None:
        assert has_ignored_part(Path("node_modules/x/index.js")) is True
        assert has_ignored_part(Path("dist/bundle.js")) is True
        assert has_ignored_part(Path(".git/HEAD")) is True

    def test_keeps_ordinary_artifact_paths(self) -> None:
        assert has_ignored_part(Path("tasks/issues/001-foo.md")) is False

    def test_extra_parts_extend_the_base_without_mutating_it(self) -> None:
        # Arrange
        extra = frozenset({"SKILL.md", "references"})

        # Act / Assert
        assert has_ignored_part(Path("references/rules.md"), extra) is True
        assert has_ignored_part(Path("SKILL.md"), extra) is True
        # Base set is unchanged for callers that pass no extras.
        assert has_ignored_part(Path("references/rules.md")) is False


class TestFixtureInputFiles:
    def test_returns_sorted_inputs_capped_at_limit(self, tmp_path: Path) -> None:
        # Arrange
        inputs = tmp_path / "fixtures" / "inputs"
        inputs.mkdir(parents=True)
        for name in ("input_b.md", "input_a.md", "input_c.md"):
            (inputs / name).write_text("x", encoding="utf-8")
        (inputs / "notes.txt").write_text("ignored", encoding="utf-8")

        # Act
        selected = fixture_input_files(tmp_path, limit=2)

        # Assert
        assert [path.name for path in selected] == ["input_a.md", "input_b.md"]

    def test_returns_empty_when_inputs_dir_absent(self, tmp_path: Path) -> None:
        assert fixture_input_files(tmp_path, limit=2) == []
