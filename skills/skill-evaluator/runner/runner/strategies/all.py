from __future__ import annotations

import time
from pathlib import Path

import structlog

from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import EvalOutcome, Mode
from runner.ports import AgentPort, JudgePort, SkillInputSizerPort, StructuralCheckPort, TriggerClassifierPort
from runner.trigger import TriggerEvaluator

_log = structlog.get_logger()


class AllStrategy:
    """Run invocation + structural checks + LLM judge + trigger routing in sequence.

    The judge and trigger run against the artifacts produced by invocation, not golden fixtures.

    Usage:
        strategy = AllStrategy(invoker, structural_runner, agent, judge_runner, judge, input_sizer, trigger_evaluator, classifier)
        outcome = strategy.run('dataviz', evals_dir)
    """

    def __init__(
        self,
        invoker: SkillInvoker,
        structural_runner: StructuralCheckPort,
        agent: AgentPort,
        judge_runner: RubricJudgeRunner,
        judge: JudgePort,
        input_sizer: SkillInputSizerPort,
        trigger_evaluator: TriggerEvaluator,
        classifier: TriggerClassifierPort,
    ) -> None:
        self._invoker = invoker
        self._structural_runner = structural_runner
        self._agent = agent
        self._judge_runner = judge_runner
        self._judge = judge
        self._input_sizer = input_sizer
        self._trigger_evaluator = trigger_evaluator
        self._classifier = classifier

    @property
    def mode(self) -> Mode:
        return "all"

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        t0 = time.monotonic()
        artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
        _log.info("invocation_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))

        t0 = time.monotonic()
        structural_results = self._structural_runner.run(evals_dir, artifacts_dir)
        _log.info("structural_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))

        t0 = time.monotonic()
        verdicts = self._judge_runner.run(evals_dir, artifacts_dir, self._judge)
        _log.info("judge_phase_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1), verdicts=len(verdicts))

        t0 = time.monotonic()
        trigger_report = self._trigger_evaluator.evaluate(skill_name, evals_dir, self._classifier)
        _log.info("trigger_phase_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1), passed=trigger_report.passed)

        return EvalOutcome(
            mode="all",
            structural_results=structural_results,
            judge_verdicts=verdicts,
            trigger_report=trigger_report,
            input_sizes=input_sizes,
        )
