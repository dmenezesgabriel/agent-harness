"""CLI entry point for running skill benchmarks.

Examples:
  # Test plan-it on pi agent, 3 trials
  uv run python run.py --skill plan-it --platform pi-agent --trials 3

  # Test implement-it on Claude Code
  uv run python run.py --skill implement-it --platform claude-code --trials 3

  # OpenCode, specific task only
  uv run python run.py --skill plan-it --platform opencode --trials 3 --task-ids plan-it-001

  # Skill variant experiment: compare modified SKILL.md vs original
  #   1. Copy skills/plan-it to skills/plan-it-v2, edit the copy
  #   2. Run with --skill-dir to point at the variant
  uv run python run.py --skill plan-it --platform pi-agent --trials 5 --skill-dir skills/plan-it-v2

  # Enable LLM judge (uses claude-haiku to avoid self-enhancement bias)
  uv run python run.py --skill plan-it --platform pi-agent --trials 5 --judge
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from harness.adapters.claude_code import ClaudeCodeAdapter
from harness.adapters.opencode import OpenCodeAdapter
from harness.adapters.pi_agent import PiAgentAdapter
from harness.models import ExperimentSummary
from harness.runner import run_experiment
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
    raise ValueError(f"Unknown platform '{platform}'. Choose: pi-agent, claude-code, opencode")


def _print_summary(summary: ExperimentSummary, skill_dir: str | None) -> None:
    variant_note = f"  skill variant: {skill_dir}" if skill_dir else ""
    table = Table(
        title=(
            f"Results: {summary.skill} on {summary.platform}"
            f"  ({summary.n_tasks} tasks × {summary.n_trials} trials){variant_note}"
        )
    )
    table.add_column("Metric", style="cyan")
    table.add_column("With skill (mean±std)", style="green")
    table.add_column("Without skill (mean±std)", style="yellow")
    table.add_column("Δ", style="bold")
    table.add_column("p-value")
    table.add_column("Cohen's d")

    metrics_to_show = [
        ("accuracy", "Accuracy"),
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1", "F1"),
        ("quality_score", "Quality Score (0-10)"),
        ("test_pass_rate", "Test Pass Rate"),
        ("judge_score", "Judge Score (0-10)"),
        ("latency_ms", "Latency (ms)"),
        ("input_tokens", "Input Tokens"),
        ("output_tokens", "Output Tokens"),
        ("total_tokens", "Total Tokens"),
    ]

    for key, label in metrics_to_show:
        w_mean, w_std = summary.with_skill.get(key, (0.0, 0.0))
        wo_mean, wo_std = summary.without_skill.get(key, (0.0, 0.0))
        delta = w_mean - wo_mean
        pval = summary.p_values.get(key, 1.0)
        eff = summary.effect_sizes.get(key, 0.0)
        sig = "*" if pval < 0.05 else ""
        delta_str = f"{delta:+.3f}{sig}"

        table.add_row(
            label,
            f"{w_mean:.3f} ± {w_std:.3f}",
            f"{wo_mean:.3f} ± {wo_std:.3f}",
            delta_str,
            f"{pval:.4f}" if pval < 0.5 else "n.s.",
            f"{eff:.2f}",
        )

    console.print(table)
    console.print("[dim]* p<0.05 (Wilcoxon signed-rank). Effect size: Cohen's d.[/dim]")
    console.print("[dim]MLflow UI: cd benchmarks && mlflow ui --backend-store-uri file://./mlruns[/dim]")


@click.command()
@click.option("--skill", required=True, help="Skill: plan-it, implement-it")
@click.option("--platform", required=True, help="Platform: pi-agent, claude-code, opencode")
@click.option("--model", default="openai-codex/gpt-5.4-mini", show_default=True, help="Model ID in provider/model format (e.g. openai-codex/gpt-5.4-mini, anthropic/claude-sonnet-4-6)")
@click.option("--trials", default=3, show_default=True, help="Trials per task per condition (10 recommended for publication)")
@click.option("--judge/--no-judge", default=False, help="Run LLM judge (uses claude-haiku, different model = no self-enhancement bias)")
@click.option("--task-ids", default=None, help="Comma-separated task IDs (default: all tasks for the skill)")
@click.option("--skill-dir", default=None, help="Path to a skill variant directory (for fine-tuning experiments)")
@click.option("--with-skill-only", is_flag=True, default=False, help="Skip without-skill condition (saves ~half the runs when comparing variants)")
@click.option("--tracking-uri", default=None, help="MLflow tracking URI override")
def main(
    skill: str,
    platform: str,
    model: str,
    trials: int,
    judge: bool,
    task_ids: str | None,
    skill_dir: str | None,
    with_skill_only: bool,
    tracking_uri: str | None,
):
    """Run a paired benchmark: with-skill vs without-skill, log everything to MLflow."""
    tasks_dir = _TASKS_DIR
    if not (tasks_dir / skill).exists():
        console.print(f"[red]No tasks found for skill '{skill}' in {tasks_dir}[/red]")
        sys.exit(1)

    try:
        adapter = _make_adapter(platform, model, skill_dir)
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    task_id_list = [t.strip() for t in task_ids.split(",")] if task_ids else None
    tracker = MLflowTracker(tracking_uri=tracking_uri)

    console.print(f"\n[bold]Benchmark:[/bold] {skill} on {platform} ({model})")
    conditions_label = "1 condition (with skill only)" if with_skill_only else "2 conditions (with / without skill)"
    console.print(f"[bold]Trials:[/bold] {trials} per task × {conditions_label}")
    if skill_dir:
        console.print(f"[bold]Skill variant:[/bold] {skill_dir}")
    console.print(f"[bold]LLM judge:[/bold] {'enabled (claude-haiku)' if judge else 'disabled'}\n")

    summary = run_experiment(
        adapter=adapter,
        skill=skill,
        tasks_dir=tasks_dir,
        n_trials=trials,
        use_judge=judge,
        tracker=tracker,
        task_ids=task_id_list,
        skill_dir=skill_dir,
        with_skill_only=with_skill_only,
    )

    _print_summary(summary, skill_dir)


if __name__ == "__main__":
    main()
