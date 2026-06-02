from __future__ import annotations

import time
from pathlib import Path

from runner.models import EvalOutcome, Mode
from runner.ports import SkillInputSizerPort, TriggerClassifierPort
from runner.strategies._timing import _log_elapsed
from runner.trigger import TriggerEvaluator


class TriggerStrategy:
    """Evaluate skill routing accuracy using eval_queries.json.

    Usage:
        strategy = TriggerStrategy(trigger_evaluator, classifier, input_sizer)
        outcome = strategy.run('dataviz', evals_dir)
    """

    def __init__(
        self,
        trigger_evaluator: TriggerEvaluator,
        classifier: TriggerClassifierPort,
        input_sizer: SkillInputSizerPort,
    ) -> None:
        self._trigger_evaluator = trigger_evaluator
        self._classifier = classifier
        self._input_sizer = input_sizer

    @property
    def mode(self) -> Mode:
        return Mode.TRIGGER

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        start = time.monotonic()
        trigger_report = self._trigger_evaluator.evaluate(
            skill_name, evals_dir, self._classifier
        )
        _log_elapsed(
            "trigger_phase_done", skill_name, start, passed=trigger_report.passed
        )

        return EvalOutcome(
            mode=Mode.TRIGGER,
            trigger_report=trigger_report,
            input_sizes=input_sizes,
        )
