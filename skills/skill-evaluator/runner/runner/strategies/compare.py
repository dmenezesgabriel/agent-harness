from __future__ import annotations

import time
from pathlib import Path

from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import EvalOutcome, Mode
from runner.ports import (
    AgentPort,
    BaselineAgentPort,
    JudgePort,
    SkillInputSizerPort,
    StructuralCheckPort,
)
from runner.strategies._timing import _log_elapsed


class CompareStrategy:
    """Invoke the skill and a plain baseline, run structural checks and judge on both.

    The baseline reveals what Claude produces without skill guidance.
    Comparing structural and judge results shows what the skill actually contributes.

    Usage:
        strategy = CompareStrategy(invoker, structural_runner, agent, baseline_agent, input_sizer, judge_runner, judge)
        outcome = strategy.run('dataviz', evals_dir)
    """

    def __init__(
        self,
        invoker: SkillInvoker,
        structural_runner: StructuralCheckPort,
        agent: AgentPort,
        baseline_agent: BaselineAgentPort,
        input_sizer: SkillInputSizerPort,
        judge_runner: RubricJudgeRunner,
        judge: JudgePort,
    ) -> None:
        self._invoker = invoker
        self._structural_runner = structural_runner
        self._agent = agent
        self._baseline_agent = baseline_agent
        self._input_sizer = input_sizer
        self._judge_runner = judge_runner
        self._judge = judge

    @property
    def mode(self) -> Mode:
        return Mode.COMPARE

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)

        start = time.monotonic()
        artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
        _log_elapsed("invocation_done", skill_name, start)

        start = time.monotonic()
        structural_results = self._structural_runner.run(evals_dir, artifacts_dir)
        _log_elapsed("structural_done", skill_name, start)

        start = time.monotonic()
        judge_verdicts = self._judge_runner.run(evals_dir, artifacts_dir, self._judge)
        _log_elapsed(
            "judge_phase_done", skill_name, start, verdicts=len(judge_verdicts)
        )

        start = time.monotonic()
        baseline_dir = self._invoker.invoke_baseline(evals_dir, self._baseline_agent)
        _log_elapsed("baseline_invocation_done", skill_name, start)

        start = time.monotonic()
        baseline_results = self._structural_runner.run(evals_dir, baseline_dir)
        _log_elapsed("baseline_structural_done", skill_name, start)

        start = time.monotonic()
        baseline_judge_verdicts = self._judge_runner.run(
            evals_dir, baseline_dir, self._judge, generated_only=True
        )
        _log_elapsed(
            "baseline_judge_phase_done",
            skill_name,
            start,
            verdicts=len(baseline_judge_verdicts),
        )

        return EvalOutcome(
            mode=Mode.COMPARE,
            structural_results=structural_results,
            baseline_structural_results=baseline_results,
            judge_verdicts=judge_verdicts,
            baseline_judge_verdicts=baseline_judge_verdicts,
            input_sizes=input_sizes,
        )
