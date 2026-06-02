from __future__ import annotations

import time
from pathlib import Path

from runner.exceptions import ProviderAbortError
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
    SkillInputSizerPort,
    StructuralCheckPort,
    TriggerClassifierPort,
)
from runner.strategies._timing import _log_elapsed
from runner.trigger import TriggerEvaluator


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
        return Mode.ALL

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        start = time.monotonic()
        artifacts_dir = evals_dir / "fixtures" / "golden"
        structural_results: list[ScenarioResult] = []
        judge_verdicts: list[JudgeReport] = []
        invocation_failure: str | None = None
        try:
            artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
        except ProviderAbortError as exc:
            invocation_failure = str(exc)
            structural_results.append(_phase_failure("invocation", invocation_failure))
        _log_elapsed("invocation_done", skill_name, start)

        if not structural_results:
            start = time.monotonic()
            try:
                structural_results = self._structural_runner.run(
                    evals_dir, artifacts_dir
                )
            except ProviderAbortError as exc:
                structural_results = [_phase_failure("structural", str(exc))]
            _log_elapsed("structural_done", skill_name, start)

        start = time.monotonic()
        if invocation_failure is not None:
            judge_verdicts = [
                _judge_failure(
                    f"skipped because invocation failed: {invocation_failure}"
                )
            ]
        else:
            try:
                judge_verdicts = self._judge_runner.run(
                    evals_dir, artifacts_dir, self._judge
                )
            except ProviderAbortError as exc:
                judge_verdicts = [_judge_failure(str(exc))]
        _log_elapsed(
            "judge_phase_done", skill_name, start, verdicts=len(judge_verdicts)
        )

        start = time.monotonic()
        try:
            trigger_report = self._trigger_evaluator.evaluate(
                skill_name, evals_dir, self._classifier
            )
        except ProviderAbortError as exc:
            trigger_report = _trigger_failure(str(exc))
        _log_elapsed(
            "trigger_phase_done", skill_name, start, passed=trigger_report.passed
        )

        return EvalOutcome(
            mode=Mode.ALL,
            structural_results=structural_results,
            judge_verdicts=judge_verdicts,
            trigger_report=trigger_report,
            input_sizes=input_sizes,
        )


def _phase_failure(phase: str, failure: str) -> ScenarioResult:
    return ScenarioResult(
        feature="skill-evaluator phase",
        scenario=f"{phase} phase completed",
        status="failed",
        failure=failure,
    )


def _judge_failure(reasoning: str) -> JudgeReport:
    return JudgeReport(
        rubric_id="judge_phase",
        passed=False,
        score=0.0,
        reasoning=reasoning,
    )


def _trigger_failure(reasoning: str) -> TriggerReport:
    return TriggerReport(
        results=[TriggerResult(query=reasoning, expected=True, actual=False)],
        pass_rate=0.0,
        passed=False,
    )
