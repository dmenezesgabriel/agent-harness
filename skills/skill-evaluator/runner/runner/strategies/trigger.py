from __future__ import annotations

import time
from pathlib import Path

import structlog

from runner.models import EvalOutcome, Mode
from runner.ports import SkillInputSizerPort, TriggerClassifierPort
from runner.trigger import TriggerEvaluator

_log = structlog.get_logger()


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
        return "trigger"

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        t0 = time.monotonic()
        trigger_report = self._trigger_evaluator.evaluate(skill_name, evals_dir, self._classifier)
        _log.info("trigger_phase_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1), passed=trigger_report.passed)

        return EvalOutcome(
            mode="trigger",
            trigger_report=trigger_report,
            input_sizes=input_sizes,
        )
