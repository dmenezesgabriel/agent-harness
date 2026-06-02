from pathlib import Path

from runner.eval_layout import has_ignored_part


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
