from __future__ import annotations

import time
from pathlib import Path

from runner.exceptions import ProviderAbortError
from runner.judging import RubricJudgeRunner
from runner.models import EvalOutcome, JudgeReport, Mode
from runner.ports import JudgePort, SkillInputSizerPort
from runner.strategies._timing import _log_elapsed


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
        return Mode.JUDGE

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome:
        input_sizes = self._input_sizer.measure(evals_dir)
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        artifacts_dir = (
            generated_dir
            if generated_dir.exists()
            else evals_dir / "fixtures" / "golden"
        )

        start = time.monotonic()
        try:
            verdicts = self._judge_runner.run(evals_dir, artifacts_dir, self._judge)
        except ProviderAbortError as exc:
            verdicts = [
                JudgeReport(
                    rubric_id="judge_provider",
                    passed=False,
                    score=0.0,
                    reasoning=str(exc),
                )
            ]
            _log_elapsed("judge_phase_aborted", skill_name, start, reason=str(exc))
            return EvalOutcome(
                mode=Mode.JUDGE,
                judge_verdicts=verdicts,
                input_sizes=input_sizes,
            )
        _log_elapsed("judge_phase_done", skill_name, start, verdicts=len(verdicts))

        return EvalOutcome(
            mode=Mode.JUDGE,
            judge_verdicts=verdicts,
            input_sizes=input_sizes,
        )
