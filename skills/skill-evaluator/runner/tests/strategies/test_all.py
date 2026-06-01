from pathlib import Path
from typing import cast

from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import (
    EvalOutcome,
    JudgeReport,
    Mode,
    ScenarioResult,
    TriggerReport,
    TriggerResult,
)
from runner.ports import (
    AgentPort,
    JudgePort,
    JudgeVerdict,
    SkillInputSizerPort,
    StructuralCheckPort,
    TriggerClassifierPort,
)
from runner.strategies.all import AllStrategy
from runner.trigger import TriggerEvaluator


class FakeInvoker:
    def __init__(self, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir

    def invoke(self, _skill_name: str, _evals_dir: Path, _agent: object) -> Path:
        return self._artifacts_dir


class FakeStructuralRunner:
    def __init__(self, results: list[ScenarioResult]) -> None:
        self._results = results

    def run(self, _evals_dir: Path, _artifacts_dir: Path) -> list[ScenarioResult]:
        return self._results


class FakeJudgeRunner:
    def __init__(self, verdicts: list[JudgeReport]) -> None:
        self._verdicts = verdicts

    def run(
        self, _evals_dir: Path, _artifacts_dir: Path, _judge: object
    ) -> list[JudgeReport]:
        return self._verdicts


class FakeJudge:
    def judge(self, _content: str, _rubric: str, rubric_id: str) -> JudgeVerdict:
        return JudgeVerdict(rubric_id=rubric_id, passed=True, score=0.9, reasoning="ok")


class FakeSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 300}


class FakeTriggerEvaluator:
    def __init__(self, report: TriggerReport) -> None:
        self._report = report

    def evaluate(
        self, _skill_name: str, _evals_dir: Path, _classifier: object
    ) -> TriggerReport:
        return self._report


class FakeClassifier:
    def classify(self, _description: str, _query: str) -> bool:
        return True


_PASSING_TRIGGER = TriggerReport(
    results=[TriggerResult(query="plot this", expected=True, actual=True)],
    pass_rate=1.0,
    passed=True,
)


def _make_strategy(
    tmp_path: Path,
    structural_results: list[ScenarioResult] | None = None,
    judge_verdicts: list[JudgeReport] | None = None,
) -> AllStrategy:
    artifacts_dir = tmp_path / "fixtures" / "_generated_artifacts"
    artifacts_dir.mkdir(parents=True)
    return AllStrategy(
        cast(SkillInvoker, FakeInvoker(artifacts_dir)),
        cast(StructuralCheckPort, FakeStructuralRunner(structural_results or [])),
        cast(AgentPort, object()),
        cast(RubricJudgeRunner, FakeJudgeRunner(judge_verdicts or [])),
        cast(JudgePort, FakeJudge()),
        cast(SkillInputSizerPort, FakeSizer()),
        cast(TriggerEvaluator, FakeTriggerEvaluator(_PASSING_TRIGGER)),
        cast(TriggerClassifierPort, FakeClassifier()),
    )


class TestAllStrategy:
    def test_mode_is_all(self, tmp_path: Path) -> None:
        assert _make_strategy(tmp_path).mode == Mode.ALL

    def test_run_returns_combined_structural_judge_and_trigger_results(
        self, tmp_path: Path
    ) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        passed = ScenarioResult(feature="f", scenario="s", status="passed")
        verdict = JudgeReport(rubric_id="q", passed=True, score=0.9, reasoning="good")

        outcome = _make_strategy(tmp_path, [passed], [verdict]).run(
            "dataviz", evals_dir
        )

        assert outcome.mode == Mode.ALL
        assert outcome.structural_results == [passed]
        assert outcome.judge_verdicts == [verdict]
        assert outcome.trigger_report == _PASSING_TRIGGER
        assert outcome.input_sizes == {"SKILL.md": 300}

    def test_run_returns_empty_results_when_no_checks_defined(
        self, tmp_path: Path
    ) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)

        outcome: EvalOutcome = _make_strategy(tmp_path).run("dataviz", evals_dir)

        assert outcome.structural_results == []
        assert outcome.judge_verdicts == []
