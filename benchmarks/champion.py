"""Champion/challenger skill variant registry.

bench-promote  — mark a skill variant as champion by content hash
bench-compare  — compare all variants for a skill side-by-side
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

import click
import mlflow
from mlflow import MlflowClient
from rich.console import Console
from rich.table import Table

console = Console()

_MLRUNS_DIR = str(Path(__file__).parent / "mlruns")


def _get_client(tracking_uri: str | None) -> MlflowClient:
    uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", f"file://{_MLRUNS_DIR}")
    mlflow.set_tracking_uri(uri)
    return MlflowClient()


def _find_skill_experiments(client: MlflowClient, skill: str) -> list[str]:
    """Return experiment IDs whose name starts with '<skill>__'."""
    prefix = f"{skill}__"
    exps = client.search_experiments()
    return [e.experiment_id for e in exps if e.name.startswith(prefix)]


def _get_summary_runs(client: MlflowClient, experiment_ids: list[str]) -> list:
    """Return all runs tagged run_type=summary across the given experiments."""
    if not experiment_ids:
        return []
    return client.search_runs(
        experiment_ids=experiment_ids,
        filter_string="tags.run_type = 'summary'",
        max_results=200,
    )


@click.command("bench-promote")
@click.option("--skill", required=True, help="Skill name (e.g. plan-it)")
@click.option("--content-hash", required=True, help="skill_content_hash to promote (e.g. sha256:a3f1b2c4)")
@click.option("--tracking-uri", default=None, help="MLflow tracking URI override")
def promote(skill: str, content_hash: str, tracking_uri: str | None):
    """Mark a skill variant as champion by its content hash."""
    client = _get_client(tracking_uri)
    exp_ids = _find_skill_experiments(client, skill)
    runs = _get_summary_runs(client, exp_ids)

    # find the target run
    target_runs = [r for r in runs if r.data.tags.get("skill_content_hash") == content_hash]
    if not target_runs:
        console.print(f"[red]No summary run found with skill_content_hash={content_hash!r} for skill '{skill}'.[/red]")
        console.print(f"[dim]Known hashes: {sorted({r.data.tags.get('skill_content_hash', '?') for r in runs})}[/dim]")
        sys.exit(1)

    # remove champion from any previous holder
    for r in runs:
        if r.data.tags.get("champion") == "true" and r.info.run_id not in {t.info.run_id for t in target_runs}:
            client.delete_tag(r.info.run_id, "champion")

    # set champion on all matching runs (multiple platforms may share the same hash)
    for r in target_runs:
        client.set_tag(r.info.run_id, "champion", "true")

    console.print(f"[bold green]★ Promoted {content_hash} as champion for '{skill}' ({len(target_runs)} run(s) tagged).[/bold green]")


@click.command("bench-compare")
@click.option("--skill", required=True, help="Skill name (e.g. plan-it)")
@click.option("--tracking-uri", default=None, help="MLflow tracking URI override")
def compare(skill: str, tracking_uri: str | None):
    """Compare all skill variants for a skill, with champion highlighted."""
    client = _get_client(tracking_uri)
    exp_ids = _find_skill_experiments(client, skill)
    runs = _get_summary_runs(client, exp_ids)

    if not runs:
        console.print(f"[yellow]No summary runs found for skill '{skill}'. Run bench-run first.[/yellow]")
        return

    # group by content hash
    groups: dict[str, list] = defaultdict(list)
    for r in runs:
        h = r.data.tags.get("skill_content_hash", "unknown")
        groups[h].append(r)

    def _mean(run_group, metric: str) -> float:
        vals = [r.data.metrics.get(metric) for r in run_group if r.data.metrics.get(metric) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    # build rows
    rows = []
    has_champion = False
    for h, group in groups.items():
        is_champ = any(r.data.tags.get("champion") == "true" for r in group)
        if is_champ:
            has_champion = True
        platforms = ", ".join(sorted({r.data.tags.get("platform", "?") for r in group}))
        trials = sum(int(r.data.tags.get("n_trials", 0)) for r in group)
        rows.append({
            "hash": h,
            "champion": is_champ,
            "platform": platforms,
            "trials": trials,
            "behave_pass_rate": _mean(group, "metrics__behave_pass_rate__mean"),
            "f1": _mean(group, "metrics__f1__mean"),
            "quality_score": _mean(group, "metrics__quality_score__mean"),
            "latency_ms": _mean(group, "metrics__latency_ms__mean"),
        })

    # sort: champion first, then by f1 descending
    rows.sort(key=lambda r: (not r["champion"], -r["f1"]))

    table = Table(title=f"Skill variants: {skill}", show_lines=True)
    table.add_column("Hash", style="cyan")
    table.add_column("Champion", justify="center")
    table.add_column("Platform")
    table.add_column("Trials", justify="right")
    table.add_column("Behave pass", justify="right")
    table.add_column("F1", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Latency (ms)", justify="right")

    for row in rows:
        champ_label = "[bold green]★ champion[/bold green]" if row["champion"] else ""
        style = "bold green" if row["champion"] else ""
        table.add_row(
            row["hash"][:23],  # sha256: + 16 chars
            champ_label,
            row["platform"],
            str(row["trials"]),
            f"{row['behave_pass_rate']:.2f}",
            f"{row['f1']:.3f}",
            f"{row['quality_score']:.3f}",
            f"{row['latency_ms']:.0f}",
            style=style,
        )

    console.print(table)

    if not has_champion:
        console.print(
            f"\n[yellow]No champion designated. Run:[/yellow]\n"
            f"  [dim]bench-promote --skill {skill} --content-hash <hash>[/dim]"
        )
