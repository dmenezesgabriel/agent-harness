"""Benchmark runner: orchestrates adapters, evaluators, and tracking.

For each task:
  - run once with the skill
  - apply task.evaluators pipeline in declaration order
  - log the result to the tracker
  - aggregate and return RunSummary
"""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

import harness.evaluators  # registers built-in evaluators in evaluator_registry

from harness.adapters.base import AgentAdapter
from harness.skill_hash import compute_skill_hash
from harness.evaluators.metrics import mean_std
from harness.models import RunSummary, Task, TaskResult
from harness.registry import evaluator_registry
from harness.tracking.base import Tracker

console = Console()

_REPO_ROOT = Path(__file__).parent.parent.parent

_SCALAR_METRICS = [
    "accuracy", "precision", "recall", "f1",
    "quality_score", "test_pass_rate", "behave_pass_rate", "judge_score",
    "latency_ms", "input_tokens", "output_tokens", "total_tokens",
]


def _load_tasks(tasks_dir: Path, skill: str) -> list[Task]:
    skill_dir = tasks_dir / skill
    if not skill_dir.exists():
        raise FileNotFoundError(f"No tasks found for skill '{skill}' in {tasks_dir}")
    tasks = []
    for p in sorted(skill_dir.glob("*.json")):
        raw = json.loads(p.read_text())
        tasks.append(Task.from_dict(raw))
    return tasks


def run_experiment(
    adapter: AgentAdapter,
    skill: str,
    tasks_dir: Path,
    tracker: Tracker,
    task_ids: list[str] | None = None,
    skill_dir: str | None = None,
) -> RunSummary:
    tasks = _load_tasks(tasks_dir, skill)
    if task_ids:
        tasks = [t for t in tasks if t.id in task_ids]
    if not tasks:
        raise ValueError(f"No tasks to run for skill '{skill}'")

    # Resolve skill directory for hash and snapshot
    _skill_dir = Path(skill_dir) if skill_dir else _REPO_ROOT / "skills" / skill
    skill_content_hash = compute_skill_hash(_skill_dir) if _skill_dir.is_dir() else None

    all_metrics: dict[str, list[float]] = {m: [] for m in _SCALAR_METRICS}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        outer = progress.add_task(f"[cyan]{skill} on {adapter.name}", total=len(tasks))

        for task in tasks:
            progress.update(outer, description=f"[cyan]{task.id}")

            result = adapter.run(task)
            for ev_name in task.evaluators:
                ev = evaluator_registry.resolve(ev_name)
                result = ev.evaluate(result, task)

            tracker.log_result(result, task, skill_dir=skill_dir, skill_content_hash=skill_content_hash)

            for m in _SCALAR_METRICS:
                all_metrics[m].append(getattr(result, m, 0.0))

            progress.advance(outer)

    # aggregate
    metrics_agg = {m: mean_std(all_metrics[m]) for m in _SCALAR_METRICS}

    summary = RunSummary(
        skill=skill,
        platform=adapter.name,
        n_tasks=len(tasks),
        metrics=metrics_agg,
    )
    tracker.log_summary(
        summary,
        skill_content_hash=skill_content_hash,
        skill_snapshot_dir=_skill_dir if _skill_dir.is_dir() else None,
    )
    return summary


class BenchmarkRunner:
    def __init__(self, tracker: Tracker) -> None:
        self._tracker = tracker

    def run_experiment(
        self,
        adapter: AgentAdapter,
        skill: str,
        tasks_dir: Path,
        task_ids: list[str] | None = None,
        skill_dir: str | None = None,
    ) -> RunSummary:
        return run_experiment(
            adapter=adapter,
            skill=skill,
            tasks_dir=tasks_dir,
            tracker=self._tracker,
            task_ids=task_ids,
            skill_dir=skill_dir,
        )
