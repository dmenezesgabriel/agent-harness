from __future__ import annotations

import sys
from pathlib import Path

from runner.discovery import SkillDiscovery
from runner.models import CliArgs, EvalOutcome
from runner.ports import EvalModeStrategy, ReportWriterPort


class SkillEvaluationApp:
    """Run skill evaluation for the requested CLI arguments.

    Usage:
        exit_code = app.run(CliArgs(skill='plan-it'))
    """

    def __init__(self, discovery: SkillDiscovery, evaluator: SkillEvaluator) -> None:
        self._discovery = discovery
        self._evaluator = evaluator

    def run(self, args: CliArgs) -> int:
        skill_dirs = self._discovery.discover(args.skill)
        if not skill_dirs:
            print(
                f"No evals found under {self._discovery.skills_root}", file=sys.stderr
            )
            return 1

        all_succeeded = True
        for evals_dir in skill_dirs:
            skill_succeeded = self._evaluator.evaluate(evals_dir)
            all_succeeded = all_succeeded and skill_succeeded
        return 0 if all_succeeded else 1


class SkillEvaluator:
    """Evaluate one skill by delegating to a mode strategy, then writing the report.

    Usage:
        ok = evaluator.evaluate(Path('skills/dataviz/evals'))
    """

    def __init__(
        self,
        strategy: EvalModeStrategy,
        report_writer: ReportWriterPort,
    ) -> None:
        self._strategy = strategy
        self._report_writer = report_writer

    def evaluate(self, evals_dir: Path) -> bool:
        skill_name = evals_dir.parent.name
        _print_skill_header(skill_name, self._strategy.mode)
        outcome = self._strategy.run(skill_name, evals_dir)
        report_path = self._report_writer.write(
            skill_name,
            evals_dir,
            outcome.mode,
            outcome.structural_results,
            outcome.judge_verdicts,
            outcome.input_sizes,
            outcome.trigger_report,
            baseline_structural_results=outcome.baseline_structural_results or None,
            baseline_judge_verdicts=outcome.baseline_judge_verdicts or None,
        )
        print(f"\nReport: {report_path}")
        return _is_successful(outcome)


def _print_skill_header(skill_name: str, mode: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"Evaluating skill: {skill_name}  (mode: {mode})")
    print(f"{'=' * 60}")


def _is_successful(outcome: EvalOutcome) -> bool:
    failed_structural = sum(
        1 for r in outcome.structural_results if r.status == "failed"
    )
    failed_judge = sum(1 for v in outcome.judge_verdicts if not v.passed)
    trigger_failed = (
        outcome.trigger_report is not None and not outcome.trigger_report.passed
    )
    return failed_structural == 0 and failed_judge == 0 and not trigger_failed
