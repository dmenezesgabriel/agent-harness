#!/usr/bin/env python3
"""Skill evaluator CLI entrypoint.

Discovers skills/*/evals/, builds the requested evaluation mode strategy,
and runs the evaluator. Modes: invoke (skill + structural), judge (LLM rubric),
trigger (routing accuracy), all (invoke + judge).

Usage:
    uv run python -m runner.run [--skill <name>] [--mode invoke|judge|all|trigger]
    uv run python -m runner.run --skill plan-it
    uv run python -m runner.run --skill dataviz --mode trigger
"""

import argparse
import os
from pathlib import Path
from typing import Protocol, cast

from runner.adapters.behave import BehaveStructuralRunner
from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.adapters.opencode import OpenCodeAdapter
from runner.discovery import SkillDiscovery
from runner.evaluation import SkillEvaluationApp, SkillEvaluator
from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.log_setup import configure as _configure_logging
from runner.models import CliArgs
from runner.ports import AgentPort, EvalModeStrategy, JudgePort, TriggerClassifierPort
from runner.reporting import MarkdownReportWriter, SkillInputSizer
from runner.strategies import AllStrategy, InvokeStrategy, JudgeStrategy, TriggerStrategy
from runner.trigger import TriggerEvaluator

_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent  # agent-harness/skills/
_MODES = ("invoke", "judge", "all", "trigger")
_ADAPTERS = ("claude", "opencode")


class _EvaluationAdapter(AgentPort, JudgePort, Protocol):
    pass


def main() -> None:
    _configure_logging()
    args = _parse_args()
    raise SystemExit(_build_app(args).run(args))


def _build_app(args: CliArgs) -> SkillEvaluationApp:
    adapter = _build_adapter(args)
    strategy = _build_strategy(args, adapter)
    evaluator = SkillEvaluator(strategy=strategy, report_writer=MarkdownReportWriter())
    return SkillEvaluationApp(discovery=SkillDiscovery(_SKILLS_ROOT), evaluator=evaluator)


def _build_strategy(args: CliArgs, adapter: _EvaluationAdapter) -> EvalModeStrategy:
    sizer = SkillInputSizer()
    match args.mode:
        case "invoke":
            return InvokeStrategy(SkillInvoker(), BehaveStructuralRunner(), cast(AgentPort, adapter), sizer)
        case "judge":
            return JudgeStrategy(RubricJudgeRunner(), cast(JudgePort, adapter), sizer)
        case "trigger":
            return TriggerStrategy(TriggerEvaluator(), cast(TriggerClassifierPort, adapter), sizer)
        case "all":
            return AllStrategy(
                SkillInvoker(), BehaveStructuralRunner(), cast(AgentPort, adapter),
                RubricJudgeRunner(), cast(JudgePort, adapter), sizer,
            )
        case _:
            raise ValueError(f"Unknown mode {args.mode!r}; expected one of {_MODES}")


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
