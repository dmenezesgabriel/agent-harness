from __future__ import annotations

import time
from pathlib import Path

from runner.exceptions import ProviderAbortError
from runner.invocation import SkillInvoker
from runner.models import EvalOutcome, Mode, ScenarioResult
from runner.ports import AgentPort, SkillInputSizerPort, StructuralCheckPort
from runner.strategies._timing import _log_elapsed


class InvokeStrategy:
    """Invoke the skill and run structural checks on the produced artifacts.

    Usage:
        strategy = InvokeStrategy(invoker, structural_runner, agent, input_sizer)
        outcome = strategy.run('dataviz', evals_dir)
    """

    def __init__(
        self,
        invoker: SkillInvoker,
        structural_runner: StructuralCheckPort,
        agent: AgentPort,
        input_sizer: SkillInputSizerPort,
    ) -> None:
        self._invoker = invoker
        self._structural_runner = structural_runner
        self._agent = agent
        self._input_sizer = input_sizer

    @property
    def mode(self) -> Mode:
        return Mode.INVOKE

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        start = time.monotonic()
        try:
            artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
        except ProviderAbortError as exc:
            _log_elapsed("invocation_aborted", skill_name, start, reason=str(exc))
            return EvalOutcome(
                mode=Mode.INVOKE,
                structural_results=[
                    ScenarioResult(
                        feature="skill-evaluator provider",
                        scenario="invocation phase completed",
                        status="failed",
                        failure=str(exc),
                    )
                ],
                input_sizes=input_sizes,
            )
        _log_elapsed("invocation_done", skill_name, start)

        start = time.monotonic()
        structural_results = self._structural_runner.run(evals_dir, artifacts_dir)
        _log_elapsed("structural_done", skill_name, start)

        return EvalOutcome(
            mode=Mode.INVOKE,
            structural_results=structural_results,
            input_sizes=input_sizes,
        )
