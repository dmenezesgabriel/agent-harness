from __future__ import annotations

import time
from pathlib import Path

import structlog

from runner.invocation import SkillInvoker
from runner.models import EvalOutcome, Mode
from runner.ports import AgentPort, SkillInputSizerPort, StructuralCheckPort

_log = structlog.get_logger()


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
        return "invoke"

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        t0 = time.monotonic()
        artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
        _log.info("invocation_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))

        t0 = time.monotonic()
        structural_results = self._structural_runner.run(evals_dir, artifacts_dir)
        _log.info("structural_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))

        return EvalOutcome(
            mode="invoke",
            structural_results=structural_results,
            input_sizes=input_sizes,
        )
