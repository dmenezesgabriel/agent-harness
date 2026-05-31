#!/usr/bin/env python3
"""Skill evaluator CLI entrypoint.

Discovers skills/*/evals/, invokes the skill via the selected agent adapter,
runs behave for structural checks on live output, and optionally runs
LLM-as-judge on golden fixtures for qualitative rubric evaluation.

Usage:
    uv run python -m runner.run [--skill <name>] [--mode invoke|judge|all]
    uv run python -m runner.run --skill plan-it
    uv run python -m runner.run --skill dataviz --mode all
"""

import argparse
import os
from pathlib import Path
from typing import Protocol, cast

from runner.adapters.behave import BehaveStructuralRunner
from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.log_setup import configure as _configure_logging
from runner.adapters.opencode import OpenCodeAdapter
from runner.discovery import SkillDiscovery
from runner.evaluation import SkillEvaluationApp, SkillEvaluator
from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import CliArgs
from runner.ports import AgentPort, JudgePort
from runner.reporting import MarkdownReportWriter, SkillInputSizer

_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent  # agent-harness/skills/
_MODES = ("invoke", "judge", "all")
_ADAPTERS = ("claude", "opencode")


class _EvaluationAdapter(AgentPort, JudgePort, Protocol):
    pass


def main() -> None:
    _configure_logging()
    args = _parse_args()
    raise SystemExit(_build_app(args).run(args))


def _build_app(args: CliArgs) -> SkillEvaluationApp:
    agent = (
        cast(AgentPort, _build_adapter(args))
        if args.mode in ("invoke", "all")
        else None
    )
    judge = (
        cast(JudgePort, _build_adapter(args)) if args.mode in ("judge", "all") else None
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


def _build_adapter(args: CliArgs) -> _EvaluationAdapter:
    if args.adapter == "claude":
        return ClaudeCodeAdapter(skill_root=_SKILLS_ROOT)
    if args.adapter == "opencode":
        return OpenCodeAdapter(
            skill_root=_SKILLS_ROOT,
            timeout=args.opencode_timeout,
            invoke_provider=args.opencode_invoke_provider,
            invoke_model=args.opencode_invoke_model,
            judge_provider=args.opencode_judge_provider,
            judge_model=args.opencode_judge_model,
        )
    raise ValueError(f"Unknown adapter {args.adapter!r}; expected one of {_ADAPTERS}")


def _parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="Evaluate agent-harness skills")
    parser.add_argument("--skill", help="Skill name to evaluate (default: all)")
    parser.add_argument(
        "--mode",
        choices=_MODES,
        default="invoke",
        help="Evaluation mode (default: invoke)",
    )
    parser.add_argument(
        "--adapter",
        choices=_ADAPTERS,
        default="claude",
        help="Agent adapter to use (default: claude)",
    )
    _add_opencode_args(parser)
    return CliArgs.model_validate(vars(parser.parse_args()))


def _add_opencode_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--opencode-invoke-provider",
        default=os.getenv("OPENCODE_INVOKE_PROVIDER", "openai-codex"),
        help="OpenCode invocation provider (default: openai-codex)",
    )
    parser.add_argument(
        "--opencode-invoke-model",
        default=os.getenv("OPENCODE_INVOKE_MODEL", "gpt-5.4-mini"),
        help="OpenCode invocation model (default: gpt-5.4-mini)",
    )
    parser.add_argument(
        "--opencode-judge-provider",
        default=os.getenv("OPENCODE_JUDGE_PROVIDER", "openai-codex"),
        help="OpenCode judge provider (default: openai-codex)",
    )
    parser.add_argument(
        "--opencode-judge-model",
        default=os.getenv("OPENCODE_JUDGE_MODEL", "chatgpt-5.5"),
        help="OpenCode judge model (default: chatgpt-5.5)",
    )
    parser.add_argument(
        "--opencode-timeout",
        type=int,
        default=int(os.getenv("OPENCODE_TIMEOUT", "180")),
        help="OpenCode request timeout in seconds (default: 180)",
    )


if __name__ == "__main__":
    main()
