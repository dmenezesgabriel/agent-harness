from pathlib import Path
from typing import cast
from unittest.mock import Mock

from runner.invocation import SkillInvoker
from runner.models import ScenarioResult
from runner.ports import (
    AgentPort,
    BaselineAgentPort,
    SkillInputSizerPort,
    StructuralCheckPort,
)
from runner.strategies.compare import CompareStrategy


class FakeInvoker:
    def __init__(self, skill_dir: Path, baseline_dir: Path) -> None:
        self._skill_dir = skill_dir
        self._baseline_dir = baseline_dir

    def invoke(self, _skill_name: str, _evals_dir: Path, _agent: object) -> Path:
        return self._skill_dir

    def invoke_baseline(self, _evals_dir: Path, _agent: object) -> Path:
        return self._baseline_dir


class FakeSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 200}


class TestCompareStrategy:
    def test_mode_is_compare(self) -> None:
        # Arrange
        runner = Mock()
        runner.run.return_value = []
        strategy = CompareStrategy(
            cast(SkillInvoker, FakeInvoker(Path("/tmp/s"), Path("/tmp/b"))),  # nosec B108
            cast(StructuralCheckPort, runner),
            cast(AgentPort, object()),
            cast(BaselineAgentPort, object()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        # Act / Assert
        assert strategy.mode == "compare"

    def test_returns_skill_and_baseline_structural_results(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        skill_passed = ScenarioResult(
            feature="f", scenario="has_chart", status="passed"
        )
        skill_failed = ScenarioResult(
            feature="f", scenario="has_title", status="failed"
        )
        baseline_failed = ScenarioResult(
            feature="f", scenario="has_chart", status="failed"
        )
        baseline_failed2 = ScenarioResult(
            feature="f", scenario="has_title", status="failed"
        )
        structural_runner = Mock()
        structural_runner.run.side_effect = [
            [skill_passed, skill_failed],
            [baseline_failed, baseline_failed2],
        ]
        strategy = CompareStrategy(
            cast(SkillInvoker, FakeInvoker(tmp_path / "skill", tmp_path / "baseline")),
            cast(StructuralCheckPort, structural_runner),
            cast(AgentPort, object()),
            cast(BaselineAgentPort, object()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        # Act
        outcome = strategy.run("dataviz", evals_dir)

        # Assert
        assert outcome.mode == "compare"
        assert outcome.structural_results == [skill_passed, skill_failed]
        assert outcome.baseline_structural_results == [
            baseline_failed,
            baseline_failed2,
        ]
        assert outcome.judge_verdicts == []
        assert outcome.trigger_report is None
        assert outcome.input_sizes == {"SKILL.md": 200}
        assert structural_runner.run.call_count == 2

    def test_structural_runner_called_for_skill_then_baseline(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        skill_dir = tmp_path / "skill"
        baseline_dir = tmp_path / "baseline"
        structural_runner = Mock()
        structural_runner.run.return_value = []
        strategy = CompareStrategy(
            cast(SkillInvoker, FakeInvoker(skill_dir, baseline_dir)),
            cast(StructuralCheckPort, structural_runner),
            cast(AgentPort, object()),
            cast(BaselineAgentPort, object()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        # Act
        strategy.run("dataviz", evals_dir)

        # Assert — first call is for skill artifacts, second for baseline
        first_call_artifacts = structural_runner.run.call_args_list[0][0][1]
        second_call_artifacts = structural_runner.run.call_args_list[1][0][1]
        assert first_call_artifacts == skill_dir
        assert second_call_artifacts == baseline_dir
