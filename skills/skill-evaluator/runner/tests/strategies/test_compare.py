from pathlib import Path
from typing import cast
from unittest.mock import Mock

from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import JudgeReport, ScenarioResult
from runner.ports import (
    AgentPort,
    BaselineAgentPort,
    JudgePort,
    JudgeVerdict,
    SkillInputSizerPort,
    StructuralCheckPort,
)
from runner.strategies.compare import CompareStrategy

_SKILL_VERDICT = JudgeReport(
    rubric_id="palette", passed=True, score=0.9, reasoning="good"
)
_BASELINE_VERDICT = JudgeReport(
    rubric_id="palette", passed=False, score=0.6, reasoning="weak"
)


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


class FakeJudgeRunner:
    """Returns pre-configured verdicts per artifacts_dir path."""

    def __init__(
        self,
        skill_verdicts: list[JudgeReport],
        baseline_verdicts: list[JudgeReport],
        skill_dir: Path,
    ) -> None:
        self._skill_verdicts = skill_verdicts
        self._baseline_verdicts = baseline_verdicts
        self._skill_dir = skill_dir

    def run(
        self, _evals_dir: Path, artifacts_dir: Path, _judge: object
    ) -> list[JudgeReport]:
        return (
            self._skill_verdicts
            if artifacts_dir == self._skill_dir
            else self._baseline_verdicts
        )


class FakeJudge:
    def judge(self, _content: str, _rubric: str, rubric_id: str) -> JudgeVerdict:
        return JudgeVerdict(rubric_id=rubric_id, passed=True, score=1.0, reasoning="ok")


def _make_strategy(
    tmp_path: Path,
    skill_dir: Path | None = None,
    baseline_dir: Path | None = None,
    structural_runner: object | None = None,
    judge_runner: object | None = None,
) -> CompareStrategy:
    skill_dir = skill_dir or tmp_path / "skill"
    baseline_dir = baseline_dir or tmp_path / "baseline"
    if structural_runner is None:
        structural_runner = Mock()
        structural_runner.run.return_value = []
    if judge_runner is None:
        judge_runner = FakeJudgeRunner([], [], skill_dir)
    return CompareStrategy(
        cast(SkillInvoker, FakeInvoker(skill_dir, baseline_dir)),
        cast(StructuralCheckPort, structural_runner),
        cast(AgentPort, object()),
        cast(BaselineAgentPort, object()),
        cast(SkillInputSizerPort, FakeSizer()),
        cast(RubricJudgeRunner, judge_runner),
        cast(JudgePort, FakeJudge()),
    )


class TestCompareStrategy:
    def test_mode_is_compare(self, tmp_path: Path) -> None:
        assert _make_strategy(tmp_path).mode == "compare"

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
        strategy = _make_strategy(
            tmp_path,
            structural_runner=structural_runner,
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
            cast(RubricJudgeRunner, FakeJudgeRunner([], [], skill_dir)),
            cast(JudgePort, FakeJudge()),
        )

        # Act
        strategy.run("dataviz", evals_dir)

        # Assert — first call is for skill artifacts, second for baseline
        first_call_artifacts = structural_runner.run.call_args_list[0][0][1]
        second_call_artifacts = structural_runner.run.call_args_list[1][0][1]
        assert first_call_artifacts == skill_dir
        assert second_call_artifacts == baseline_dir


class TestCompareStrategyJudge:
    def test_judge_runner_called_twice_for_skill_then_baseline(
        self, tmp_path: Path
    ) -> None:
        """UT-001 / OT-001: judge_runner.run is called once per artifacts dir."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        skill_dir = tmp_path / "skill"
        baseline_dir = tmp_path / "baseline"
        judge_runner = Mock()
        judge_runner.run.return_value = []
        strategy = CompareStrategy(
            cast(SkillInvoker, FakeInvoker(skill_dir, baseline_dir)),
            cast(StructuralCheckPort, Mock(run=Mock(return_value=[]))),
            cast(AgentPort, object()),
            cast(BaselineAgentPort, object()),
            cast(SkillInputSizerPort, FakeSizer()),
            cast(RubricJudgeRunner, judge_runner),
            cast(JudgePort, FakeJudge()),
        )

        # Act
        strategy.run("dataviz", evals_dir)

        # Assert — two judge calls, first for skill dir, second for baseline dir
        assert judge_runner.run.call_count == 2
        assert judge_runner.run.call_args_list[0][0][1] == skill_dir
        assert judge_runner.run.call_args_list[1][0][1] == baseline_dir

    def test_judge_verdicts_assigned_to_correct_outcome_fields(
        self, tmp_path: Path
    ) -> None:
        """UT-002 / AC-001: skill verdicts → judge_verdicts, baseline → baseline_judge_verdicts."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        skill_dir = tmp_path / "skill"
        strategy = _make_strategy(
            tmp_path,
            skill_dir=skill_dir,
            judge_runner=FakeJudgeRunner(
                [_SKILL_VERDICT], [_BASELINE_VERDICT], skill_dir
            ),
        )

        # Act
        outcome = strategy.run("dataviz", evals_dir)

        # Assert
        assert outcome.judge_verdicts == [_SKILL_VERDICT]
        assert outcome.baseline_judge_verdicts == [_BASELINE_VERDICT]

    def test_empty_judge_verdicts_does_not_break_structural_results(
        self, tmp_path: Path
    ) -> None:
        """UT-005: no regression on structural results when judge returns empty."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        passed = ScenarioResult(feature="f", scenario="has_chart", status="passed")
        structural_runner = Mock()
        structural_runner.run.return_value = [passed]
        strategy = _make_strategy(tmp_path, structural_runner=structural_runner)

        # Act
        outcome = strategy.run("dataviz", evals_dir)

        # Assert
        assert outcome.structural_results == [passed]
        assert outcome.baseline_structural_results == [passed]
        assert outcome.judge_verdicts == []
        assert outcome.baseline_judge_verdicts == []
