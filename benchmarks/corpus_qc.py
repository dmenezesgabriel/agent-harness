"""Corpus quality check using Benchmark² meta-metrics.

Computes:
  DS  — Discriminability Score: tasks actually distinguish conditions
  CAD — Capability Alignment Deviation: hard tasks are consistently hard
  BQS — Benchmark Quality Score: 0.3*DS + 0.4*CAD + 0.3*CBRC

CBRC requires results from multiple subsets — approximated here by
random 70/30 splits.

Usage:
  uv run python corpus_qc.py --skill plan-it --platform api
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path

import click
import mlflow

_MLRUNS_DIR = str(Path(__file__).parent / "mlruns")


def _fetch_runs(skill: str, platform: str) -> list[dict]:
    mlflow.set_tracking_uri(f"file://{_MLRUNS_DIR}")
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(f"{skill}__{platform}")
    if not exp:
        return []
    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        filter_string="tags.run_type != 'summary'",
    )
    results = []
    for r in runs:
        if r.data.tags.get("run_type") == "summary":
            continue
        results.append({
            "task_id": r.data.tags.get("task_id", ""),
            "condition": r.data.tags.get("condition", ""),
            "accuracy": r.data.metrics.get("accuracy", 0.0),
            "f1": r.data.metrics.get("f1", 0.0),
        })
    return results


def _discriminability_score(runs: list[dict]) -> float:
    """DS = normalized spread × fraction of tasks with significant condition gap."""
    by_task: dict[str, dict[str, list[float]]] = {}
    for r in runs:
        tid = r["task_id"]
        cond = r["condition"]
        by_task.setdefault(tid, {"with_skill": [], "without_skill": []})
        by_task[tid][cond].append(r["accuracy"])

    if not by_task:
        return 0.0

    gaps = []
    for tid, conds in by_task.items():
        w = conds.get("with_skill", [])
        wo = conds.get("without_skill", [])
        if w and wo:
            gap = abs(sum(w) / len(w) - sum(wo) / len(wo))
            gaps.append(gap)

    if not gaps:
        return 0.0

    mean_gap = sum(gaps) / len(gaps)
    significant = sum(1 for g in gaps if g > 0.1) / len(gaps)
    return min(mean_gap * significant * 2, 1.0)


def _cad_score(runs: list[dict]) -> float:
    """CAD — penalizes inconsistency: strong condition fails where weak succeeds."""
    by_task: dict[str, dict[str, list[float]]] = {}
    for r in runs:
        tid = r["task_id"]
        cond = r["condition"]
        by_task.setdefault(tid, {"with_skill": [], "without_skill": []})
        by_task[tid][cond].append(r["accuracy"])

    inversions = 0
    total = 0
    for tid, conds in by_task.items():
        w = conds.get("with_skill", [])
        wo = conds.get("without_skill", [])
        if not w or not wo:
            continue
        mean_w = sum(w) / len(w)
        mean_wo = sum(wo) / len(wo)
        total += 1
        # inversion: without_skill outperforms with_skill
        if mean_wo > mean_w + 0.05:
            inversions += 1

    if total == 0:
        return 0.0

    inv_rate = inversions / total
    return math.exp(-12 * inv_rate)


def _cbrc_score(runs: list[dict], n_splits: int = 5) -> float:
    """CBRC — ranking consistency across random 70% subsets (Kendall's tau approximation)."""
    task_ids = list({r["task_id"] for r in runs})
    if len(task_ids) < 4:
        return 0.5  # insufficient data

    task_scores: dict[str, float] = {}
    by_task: dict[str, dict[str, list[float]]] = {}
    for r in runs:
        tid = r["task_id"]
        cond = r["condition"]
        by_task.setdefault(tid, {"with_skill": [], "without_skill": []})
        by_task[tid][cond].append(r["accuracy"])

    for tid, conds in by_task.items():
        w = conds.get("with_skill", [])
        wo = conds.get("without_skill", [])
        if w and wo:
            task_scores[tid] = sum(w) / len(w) - sum(wo) / len(wo)

    if len(task_scores) < 4:
        return 0.5

    full_ranking = sorted(task_scores, key=task_scores.get, reverse=True)

    taus = []
    for _ in range(n_splits):
        sample = random.sample(list(task_scores), k=max(2, int(len(task_scores) * 0.7)))
        subset_ranking = sorted(sample, key=task_scores.get, reverse=True)
        # Kendall's tau via concordant/discordant pairs
        concordant = discordant = 0
        for i in range(len(subset_ranking)):
            for j in range(i + 1, len(subset_ranking)):
                a, b = subset_ranking[i], subset_ranking[j]
                fi, fj = full_ranking.index(a), full_ranking.index(b)
                if fi < fj:
                    concordant += 1
                else:
                    discordant += 1
        n = len(subset_ranking)
        denom = n * (n - 1) / 2
        taus.append((concordant - discordant) / denom if denom > 0 else 0.0)

    return sum(taus) / len(taus) if taus else 0.5


@click.command()
@click.option("--skill", required=True, help="Skill name, e.g. plan-it")
@click.option("--platform", default="api", help="Platform, e.g. api, claude-code")
def main(skill: str, platform: str):
    """Compute corpus quality metrics (DS, CAD, CBRC, BQS) from MLflow runs."""
    runs = _fetch_runs(skill, platform)
    if not runs:
        click.echo(f"No runs found for {skill}__{platform}. Run experiments first.", err=True)
        sys.exit(1)

    ds = _discriminability_score(runs)
    cad = _cad_score(runs)
    cbrc = _cbrc_score(runs)
    bqs = 0.3 * ds + 0.4 * cad + 0.3 * ((cbrc + 1) / 2)

    click.echo(f"\nCorpus Quality Report: {skill} on {platform}")
    click.echo(f"  Tasks with runs : {len({r['task_id'] for r in runs})}")
    click.echo(f"  Total runs      : {len(runs)}")
    click.echo(f"  DS  (>0.2 good) : {ds:.3f}  {'OK' if ds > 0.2 else 'LOW'}")
    click.echo(f"  CAD (>0.6 good) : {cad:.3f}  {'OK' if cad > 0.6 else 'LOW'}")
    click.echo(f"  CBRC(>0.4 good) : {cbrc:.3f}  {'OK' if cbrc > 0.4 else 'LOW'}")
    click.echo(f"  BQS             : {bqs:.3f}  {'OK' if bqs > 0.4 else 'LOW'}")

    thresholds_met = sum([ds > 0.2, cad > 0.6, cbrc > 0.4])
    if thresholds_met == 3:
        click.echo("\n[PASS] Corpus quality is sufficient to trust results.")
    else:
        click.echo(f"\n[WARN] {3 - thresholds_met}/3 quality thresholds not met. Results may be unreliable.")


if __name__ == "__main__":
    main()
