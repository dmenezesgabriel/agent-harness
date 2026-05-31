#!/usr/bin/env python3
"""Skill evaluator CLI entrypoint.

Discovers skills/*/evals/, invokes the skill via claude CLI (haiku), runs behave
for structural checks on live output, and optionally runs LLM-as-judge (sonnet)
on golden fixtures for qualitative rubric evaluation.

Usage:
    uv run python -m runner.run [--skill <name>] [--mode invoke|judge|all]
    uv run python -m runner.run --skill plan-it
    uv run python -m runner.run --skill dataviz --mode all
"""

import argparse
from pathlib import Path

from runner.adapters.behave import BehaveStructuralRunner
from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.discovery import SkillDiscovery
from runner.evaluation import SkillEvaluationApp, SkillEvaluator
from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import CliArgs
from runner.reporting import MarkdownReportWriter, SkillInputSizer

_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent  # agent-harness/skills/
_MODES = ("invoke", "judge", "all")


def main() -> None:
    args = _parse_args()
    raise SystemExit(_build_app(args).run(args))


def _build_app(args: CliArgs) -> SkillEvaluationApp:
    agent = (
        ClaudeCodeAdapter(skill_root=_SKILLS_ROOT)
        if args.mode in ("invoke", "all")
        else None
    )
    judge = (
        ClaudeCodeAdapter(skill_root=_SKILLS_ROOT)
        if args.mode in ("judge", "all")
        else None
    )
    evaluator = SkillEvaluator(
        invoker=SkillInvoker(),
        structural_runner=BehaveStructuralRunner(),
        judge_runner=RubricJudgeRunner(),
        input_sizer=SkillInputSizer(),
        report_writer=MarkdownReportWriter(),
        agent=agent,
        judge=judge,
    )
    return SkillEvaluationApp(
        discovery=SkillDiscovery(_SKILLS_ROOT), evaluator=evaluator
    )


def _parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="Evaluate agent-harness skills")
    parser.add_argument("--skill", help="Skill name to evaluate (default: all)")
    parser.add_argument(
        "--mode",
        choices=_MODES,
        default="invoke",
        help="Evaluation mode (default: invoke)",
    )
    return CliArgs.model_validate(vars(parser.parse_args()))


if __name__ == "__main__":
    main()
