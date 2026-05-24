"""CLI entry point for running skill benchmarks.

Examples:
  # Test plan-it on pi agent
  uv run python run.py --skill plan-it --platform pi-agent

  # Test implement-it on Claude Code
  uv run python run.py --skill implement-it --platform claude-code

  # OpenCode, specific task only
  uv run python run.py --skill plan-it --platform opencode --task-ids plan-it-001

  # Skill variant experiment: compare modified SKILL.md vs original
  #   1. Copy skills/plan-it to skills/plan-it-v2, edit the copy
  #   2. Run with --skill-dir to point at the variant
  uv run python run.py --skill plan-it --platform pi-agent --skill-dir skills/plan-it-v2
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

import harness.adapters  # registers built-in adapters in adapter_registry

from harness.adapters.claude_code import ClaudeCodeAdapter
from harness.adapters.opencode import OpenCodeAdapter
from harness.adapters.pi_agent import PiAgentAdapter
from harness.models import RunSummary
from harness.registry import adapter_registry
from harness.runner import run_experiment
from harness.skill_lint import SkillLintValidator
from harness.tracking.null_tracker import NullTracker
from harness.tracking.tracker import MLflowTracker

console = Console()
_TASKS_DIR = Path(__file__).parent / "tasks"
_REPO_ROOT = Path(__file__).parent.parent


def _make_adapter(platform: str, model: str, skill_dir: str | None):
    if platform == "pi-agent":
        return PiAgentAdapter(model=model, skill_dir=skill_dir)
    if platform == "claude-code":
        return ClaudeCodeAdapter(model=model)
    if platform == "opencode":
        return OpenCodeAdapter(model=model)
    try:
        return adapter_registry.resolve(platform)
    except KeyError:
        known = ", ".join(adapter_registry.list_names())
        raise ValueError(
            f"Unknown platform '{platform}'. Known: {known}. "
            "Register a custom adapter via adapter_registry.register() before invoking the CLI."
        )


def _print_summary(summary: RunSummary, skill_dir: str | None) -> None:
    variant_note = f"  skill variant: {skill_dir}" if skill_dir else ""
    table = Table(
        title=(
            f"Results: {summary.skill} on {summary.platform}"
            f"  ({summary.n_tasks} tasks){variant_note}"
        )
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Mean ± Std", style="green")

    metrics_to_show = [
        ("accuracy", "Accuracy"),
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1", "F1"),
        ("quality_score", "Quality Score (0-10)"),
        ("behave_pass_rate", "Behave Pass Rate"),
        ("test_pass_rate", "Test Pass Rate"),
        ("judge_score", "Judge Score (0-10)"),
        ("latency_ms", "Latency (ms)"),
        ("input_tokens", "Input Tokens"),
        ("output_tokens", "Output Tokens"),
        ("total_tokens", "Total Tokens"),
    ]

    for key, label in metrics_to_show:
        mean, std = summary.metrics.get(key, (0.0, 0.0))
        table.add_row(label, f"{mean:.3f} ± {std:.3f}")

    console.print(table)
    console.print("[dim]MLflow UI: cd benchmarks && mlflow ui --backend-store-uri file://./mlruns[/dim]")


@click.command()
@click.option("--skill", required=True, help="Skill: plan-it, implement-it")
@click.option("--platform", required=True, help="Platform: pi-agent, claude-code, opencode")
@click.option("--model", default="openai-codex/gpt-5.4-mini", show_default=True, help="Model ID in provider/model format (e.g. openai-codex/gpt-5.4-mini, anthropic/claude-sonnet-4-6)")
@click.option("--task-ids", default=None, help="Comma-separated task IDs (default: all tasks for the skill)")
@click.option("--skill-dir", default=None, help="Path to a skill variant directory (for fine-tuning experiments)")
@click.option("--tracking-uri", default=None, help="MLflow tracking URI override")
@click.option("--dry-run", is_flag=True, default=False, help="Skip MLflow tracking (NullTracker); useful when no MLflow server is available")
def main(
    skill: str,
    platform: str,
    model: str,
    task_ids: str | None,
    skill_dir: str | None,
    tracking_uri: str | None,
    dry_run: bool,
):
    """Run a skill benchmark and log results to MLflow."""
    tasks_dir = _TASKS_DIR
    if not (tasks_dir / skill).exists():
        console.print(f"[red]No tasks found for skill '{skill}' in {tasks_dir}[/red]")
        sys.exit(1)

    actual_skill_dir = Path(skill_dir) if skill_dir else _REPO_ROOT / "skills" / skill
    lint_result = SkillLintValidator().validate(actual_skill_dir)
    if not lint_result.passed:
        for error in lint_result.errors:
            click.echo(error.message)
        sys.exit(1)

    try:
        adapter = _make_adapter(platform, model, skill_dir)
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    task_id_list = [t.strip() for t in task_ids.split(",")] if task_ids else None
    tracker = NullTracker() if dry_run else MLflowTracker(tracking_uri=tracking_uri)

    console.print(f"\n[bold]Benchmark:[/bold] {skill} on {platform} ({model})")
    if skill_dir:
        console.print(f"[bold]Skill variant:[/bold] {skill_dir}")
    console.print()

    summary = run_experiment(
        adapter=adapter,
        skill=skill,
        tasks_dir=tasks_dir,
        tracker=tracker,
        task_ids=task_id_list,
        skill_dir=skill_dir,
    )

    _print_summary(summary, skill_dir)


if __name__ == "__main__":
    main()
