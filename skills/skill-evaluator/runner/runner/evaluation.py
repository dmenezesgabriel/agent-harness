from __future__ import annotations

import sys
import time
from pathlib import Path

import structlog

_log = structlog.get_logger()

from runner.discovery import SkillDiscovery
from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import CliArgs, JudgeReport, Mode, ScenarioResult
from runner.ports import (
    AgentPort,
    JudgePort,
    ReportWriterPort,
    SkillInputSizerPort,
    StructuralCheckPort,
)


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

        overall_ok = True
        for evals_dir in skill_dirs:
            ok = self._evaluator.evaluate(evals_dir, args.mode)
            overall_ok = overall_ok and ok
        return 0 if overall_ok else 1


class SkillEvaluator:
    """Evaluate one skill through invocation, structural checks, judge, and report.

    Usage:
        ok = evaluator.evaluate(Path('skills/dataviz/evals'), 'all')
    """

    def __init__(
        self,
        invoker: SkillInvoker,
        structural_runner: StructuralCheckPort,
        judge_runner: RubricJudgeRunner,
        input_sizer: SkillInputSizerPort,
        report_writer: ReportWriterPort,
        agent: AgentPort | None,
        judge: JudgePort | None,
    ) -> None:
        self._invoker = invoker
        self._structural_runner = structural_runner
        self._judge_runner = judge_runner
        self._input_sizer = input_sizer
        self._report_writer = report_writer
        self._agent = agent
        self._judge = judge

    def evaluate(self, evals_dir: Path, mode: Mode) -> bool:
        skill_name = evals_dir.parent.name
        _print_skill_header(skill_name, mode)
        golden_dir = evals_dir / "fixtures" / "golden"
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        artifacts_dir = (
            generated_dir if mode == "judge" and generated_dir.exists() else golden_dir
        )
        input_sizes = self._input_sizer.measure(evals_dir)
        structural_results: list[ScenarioResult] = []

        if mode in ("invoke", "all") and self._agent is not None:
            t0 = time.monotonic()
            artifacts_dir = self._invoker.invoke(skill_name, evals_dir, self._agent)
            _log.info("invocation_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))
            t0 = time.monotonic()
            structural_results = self._structural_runner.run(evals_dir, artifacts_dir)
            _log.info("structural_done", skill=skill_name, elapsed_s=round(time.monotonic() - t0, 1))

        judge_verdicts = self._judge_verdicts(evals_dir, artifacts_dir, mode)
        report_path = self._report_writer.write(
            skill_name,
            evals_dir,
            mode,
            structural_results,
            judge_verdicts,
            input_sizes,
        )
        print(f"\nReport: {report_path}")
        return _is_successful(structural_results, judge_verdicts)

    def _judge_verdicts(
        self, evals_dir: Path, artifacts_dir: Path, mode: Mode
    ) -> list[JudgeReport]:
        if mode not in ("judge", "all") or self._judge is None:
            return []
        t0 = time.monotonic()
        verdicts = self._judge_runner.run(evals_dir, artifacts_dir, self._judge)
        _log.info("judge_phase_done", skill=evals_dir.parent.name, elapsed_s=round(time.monotonic() - t0, 1), verdicts=len(verdicts))
        return verdicts


def _print_skill_header(skill_name: str, mode: Mode) -> None:
    print(f"\n{'=' * 60}")
    print(f"Evaluating skill: {skill_name}  (mode: {mode})")
    print(f"{'=' * 60}")


def _is_successful(
    structural_results: list[ScenarioResult], judge_verdicts: list[JudgeReport]
) -> bool:
    failed_structural = sum(
        1 for scenario in structural_results if scenario.status == "failed"
    )
    failed_judge = sum(1 for verdict in judge_verdicts if not verdict.passed)
    return failed_structural == 0 and failed_judge == 0
