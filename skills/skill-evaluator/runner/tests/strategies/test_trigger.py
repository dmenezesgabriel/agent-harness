from pathlib import Path
from typing import cast

from runner.models import TriggerReport, TriggerResult
from runner.ports import SkillInputSizerPort, TriggerClassifierPort
from runner.strategies.trigger import TriggerStrategy
from runner.trigger import TriggerEvaluator


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


class FakeSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 50}


_PASSING_REPORT = TriggerReport(
    results=[TriggerResult(query="plot this", expected=True, actual=True)],
    pass_rate=1.0,
    passed=True,
)


class TestTriggerStrategy:
    def test_trigger_strategy_mode_is_trigger(self) -> None:
        strategy = TriggerStrategy(
            cast(TriggerEvaluator, FakeTriggerEvaluator(_PASSING_REPORT)),
            cast(TriggerClassifierPort, FakeClassifier()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        assert strategy.mode == "trigger"

    def test_trigger_strategy_returns_trigger_report(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)

        strategy = TriggerStrategy(
            cast(TriggerEvaluator, FakeTriggerEvaluator(_PASSING_REPORT)),
            cast(TriggerClassifierPort, FakeClassifier()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        outcome = strategy.run("dataviz", evals_dir)

        assert outcome.mode == "trigger"
        assert outcome.trigger_report == _PASSING_REPORT
        assert outcome.structural_results == []
        assert outcome.judge_verdicts == []
