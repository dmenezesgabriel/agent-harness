from pathlib import Path

from runner.discovery import SkillDiscovery


class TestSkillDiscovery:
    def test_discover_filters_skill_and_excludes_evaluator(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "dataviz" / "evals").mkdir(parents=True)
        (tmp_path / "plan-it" / "evals").mkdir(parents=True)
        (tmp_path / "skill-evaluator" / "evals").mkdir(parents=True)

        # Act
        eval_dirs = SkillDiscovery(tmp_path).discover("dataviz")

        # Assert
        assert eval_dirs == [tmp_path / "dataviz" / "evals"]

    def test_discover_returns_all_non_evaluator_eval_dirs(self, tmp_path: Path) -> None:
        # Arrange
        (tmp_path / "dataviz" / "evals").mkdir(parents=True)
        (tmp_path / "plan-it" / "evals").mkdir(parents=True)
        (tmp_path / "skill-evaluator" / "evals").mkdir(parents=True)

        # Act
        eval_dirs = SkillDiscovery(tmp_path).discover(None)

        # Assert
        assert eval_dirs == [
            tmp_path / "dataviz" / "evals",
            tmp_path / "plan-it" / "evals",
        ]
