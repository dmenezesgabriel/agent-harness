from pathlib import Path
from typing import cast
from unittest.mock import Mock

from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import JudgeReport, ScenarioResult
from runner.ports import (
    AgentPort,
    BaselineAgentPort,
    CompareJudgePort,
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
    """Returns pre-configured verdicts from compare_run."""

    def __init__(
        self,
        skill_verdicts: list[JudgeReport],
        baseline_verdicts: list[JudgeReport],
    ) -> None:
        self._skill_verdicts = skill_verdicts
        self._baseline_verdicts = baseline_verdicts

    def compare_run(
        self,
        _evals_dir: Path,
        _skill_dir: Path,
        _baseline_dir: Path,
        _judge: object,
    ) -> tuple[list[JudgeReport], list[JudgeReport]]:
        return self._skill_verdicts, self._baseline_verdicts


class FakeJudge:
    def judge(self, _content: str, _rubric: str, rubric_id: str) -> JudgeReport:
        return JudgeReport(rubric_id=rubric_id, passed=True, score=1.0, reasoning="ok")

    def compare_judge(
        self,
        _skill: str,
        _baseline: str,
        _rubric: str,
        rubric_id: str,
    ) -> tuple[JudgeReport, JudgeReport]:
        return (
            JudgeReport(
                rubric_id=rubric_id, passed=True, score=1.0, reasoning="skill ok"
            ),
            JudgeReport(
                rubric_id=rubric_id, passed=False, score=0.5, reasoning="baseline weak"
            ),
        )


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
        judge_runner = FakeJudgeRunner([], [])
    return CompareStrategy(
        cast(SkillInvoker, FakeInvoker(skill_dir, baseline_dir)),
        cast(StructuralCheckPort, structural_runner),
        cast(AgentPort, object()),
        cast(BaselineAgentPort, object()),
        cast(SkillInputSizerPort, FakeSizer()),
        cast(RubricJudgeRunner, judge_runner),
        cast(CompareJudgePort, FakeJudge()),
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
            cast(RubricJudgeRunner, FakeJudgeRunner([], [])),
            cast(CompareJudgePort, FakeJudge()),
        )

        # Act
        strategy.run("dataviz", evals_dir)

        # Assert — first call is for skill artifacts, second for baseline
        first_call_artifacts = structural_runner.run.call_args_list[0][0][1]
        second_call_artifacts = structural_runner.run.call_args_list[1][0][1]
        assert first_call_artifacts == skill_dir
        assert second_call_artifacts == baseline_dir


class TestCompareStrategyJudge:
    def test_compare_run_called_once_with_both_dirs(self, tmp_path: Path) -> None:
        """compare_run replaces two separate run() calls — one call, both dirs."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        skill_dir = tmp_path / "skill"
        baseline_dir = tmp_path / "baseline"
        judge_runner = Mock()
        judge_runner.compare_run.return_value = ([], [])
        strategy = CompareStrategy(
            cast(SkillInvoker, FakeInvoker(skill_dir, baseline_dir)),
            cast(StructuralCheckPort, Mock(run=Mock(return_value=[]))),
            cast(AgentPort, object()),
            cast(BaselineAgentPort, object()),
            cast(SkillInputSizerPort, FakeSizer()),
            cast(RubricJudgeRunner, judge_runner),
            cast(CompareJudgePort, FakeJudge()),
        )

        # Act
        strategy.run("dataviz", evals_dir)

        # Assert — exactly one compare_run call with skill_dir and baseline_dir
        assert judge_runner.compare_run.call_count == 1
        call_args = judge_runner.compare_run.call_args[0]
        assert call_args[1] == skill_dir
        assert call_args[2] == baseline_dir

    def test_judge_verdicts_assigned_to_correct_outcome_fields(
        self, tmp_path: Path
    ) -> None:
        """Skill verdicts → judge_verdicts, baseline verdicts → baseline_judge_verdicts."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        strategy = _make_strategy(
            tmp_path,
            judge_runner=FakeJudgeRunner([_SKILL_VERDICT], [_BASELINE_VERDICT]),
        )

        # Act
        outcome = strategy.run("dataviz", evals_dir)

        # Assert
        assert outcome.judge_verdicts == [_SKILL_VERDICT]
        assert outcome.baseline_judge_verdicts == [_BASELINE_VERDICT]

    def test_empty_judge_verdicts_does_not_break_structural_results(
        self, tmp_path: Path
    ) -> None:
        """No regression on structural results when judge returns empty."""
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
