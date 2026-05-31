from __future__ import annotations

import time
from pathlib import Path

import structlog

from runner.judging import RubricJudgeRunner
from runner.models import EvalOutcome, Mode
from runner.ports import JudgePort, SkillInputSizerPort

_log = structlog.get_logger()


class JudgeStrategy:
    """Run LLM-as-judge rubric evaluation against golden or generated artifacts.

    Prefers _generated_artifacts/ if present, falls back to golden/.

    Usage:
        strategy = JudgeStrategy(judge_runner, judge, input_sizer)
        outcome = strategy.run('dataviz', evals_dir)
    """

    def __init__(
        self,
        judge_runner: RubricJudgeRunner,
        judge: JudgePort,
        input_sizer: SkillInputSizerPort,
    ) -> None:
        self._judge_runner = judge_runner
        self._judge = judge
        self._input_sizer = input_sizer

    @property
    def mode(self) -> Mode:
        return "judge"

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        artifacts_dir = (
            generated_dir if generated_dir.exists() else evals_dir / "fixtures" / "golden"
        )

        t0 = time.monotonic()
        verdicts = self._judge_runner.run(evals_dir, artifacts_dir, self._judge)
        _log.info("judge_phase_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1), verdicts=len(verdicts))

        return EvalOutcome(
            mode="judge",
            judge_verdicts=verdicts,
            input_sizes=input_sizes,
        )
