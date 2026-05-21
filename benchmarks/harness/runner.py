"""Experiment runner: orchestrates adapters, evaluators, and MLflow tracking.

For each task:
  - run N trials under WITH_SKILL condition
  - run N trials under WITHOUT_SKILL condition
  - evaluate each trial
  - optionally run LLM judge pairwise on one pair per task
  - log all results to MLflow
  - aggregate and return ExperimentSummary with statistical tests
"""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from harness.adapters.base import AgentAdapter
from harness.skill_hash import compute_skill_hash
from harness.evaluators.base import Evaluator
from harness.evaluators.behave_evaluator import BehaveEvaluator
from harness.evaluators.code_evaluator import CodeEvaluator
from harness.evaluators.llm_judge import LLMJudge
from harness.evaluators.metrics import cohens_d, mean_std
from harness.evaluators.plan_evaluator import PlanEvaluator
from harness.models import Condition, ExperimentSummary, Task, TrialResult
from harness.tracking.tracker import MLflowTracker

console = Console()

_REPO_ROOT = Path(__file__).parent.parent.parent

_EVALUATORS: dict[str, Evaluator] = {
    "plan_evaluator": PlanEvaluator(),
    "code_evaluator": CodeEvaluator(),
}

_BEHAVE = BehaveEvaluator()

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


def _statistical_test(a: list[float], b: list[float]) -> tuple[float, float]:
    """Wilcoxon signed-rank test. Returns (p_value, cohen_d)."""
    try:
        from scipy.stats import wilcoxon
        if len(a) < 2 or len(a) != len(b):
            return 1.0, 0.0
        _, p = wilcoxon(a, b, zero_method="wilcox", alternative="two-sided")
        ma, sa = mean_std(a)
        mb, sb = mean_std(b)
        d = cohens_d(ma, mb, sa, sb)
        return float(p), d
    except Exception:
        return 1.0, 0.0


def run_experiment(
    adapter: AgentAdapter,
    skill: str,
    tasks_dir: Path,
    n_trials: int = 3,
    use_judge: bool = False,
    tracker: MLflowTracker | None = None,
    task_ids: list[str] | None = None,
    skill_dir: str | None = None,
    with_skill_only: bool = False,
) -> ExperimentSummary:
    tasks = _load_tasks(tasks_dir, skill)
    if task_ids:
        tasks = [t for t in tasks if t.id in task_ids]
    if not tasks:
        raise ValueError(f"No tasks to run for skill '{skill}'")

    # Resolve skill directory for hash and snapshot
    _skill_dir = Path(skill_dir) if skill_dir else _REPO_ROOT / "skills" / skill
    skill_content_hash = compute_skill_hash(_skill_dir) if _skill_dir.is_dir() else None

    tracker = tracker or MLflowTracker()
    judge = LLMJudge() if use_judge else None

    all_with: dict[str, list[float]] = {m: [] for m in _SCALAR_METRICS}
    all_without: dict[str, list[float]] = {m: [] for m in _SCALAR_METRICS}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        outer = progress.add_task(f"[cyan]{skill} on {adapter.name}", total=len(tasks))

        for task in tasks:
            evaluator = _EVALUATORS.get(task.evaluator, PlanEvaluator())

            with_results: list[TrialResult] = []
            without_results: list[TrialResult] = []

            for trial in range(n_trials):
                progress.update(outer, description=f"[cyan]{task.id} trial {trial+1}/{n_trials}")

                conditions = [(Condition.WITH_SKILL, with_results)]
                if not with_skill_only:
                    conditions.append((Condition.WITHOUT_SKILL, without_results))

                for condition, bucket in conditions:
                    result = adapter.run(task, condition, trial)
                    result = evaluator.evaluate(result, task)
                    result = _BEHAVE.evaluate(result)

                    if judge:
                        score, reason = judge.pointwise(result, task.title, task.instruction)
                        result.judge_score = score
                        result.judge_verdict = reason

                    tracker.log_trial(result, task, skill_dir=skill_dir, skill_content_hash=skill_content_hash)
                    bucket.append(result)

            # pairwise judge on first trial pair
            if judge and with_results and without_results:
                winner, reason = judge.pairwise(
                    with_results[0], without_results[0],
                    task.title, task.instruction,
                )
                console.print(f"  [dim]judge pairwise: {winner} — {reason}[/dim]")

            for result, bucket in [(r, all_with) for r in with_results] + [(r, all_without) for r in without_results]:
                target = all_with if result.condition == Condition.WITH_SKILL.value else all_without
                for m in _SCALAR_METRICS:
                    target[m].append(getattr(result, m, 0.0))

            progress.advance(outer)

    # aggregate
    with_agg = {m: mean_std(all_with[m]) for m in _SCALAR_METRICS}
    without_agg = {m: mean_std(all_without[m]) for m in _SCALAR_METRICS}
    p_values = {}
    effect_sizes = {}
    for m in ["accuracy", "precision", "recall", "f1", "quality_score", "test_pass_rate", "behave_pass_rate"]:
        p, d = _statistical_test(all_with[m], all_without[m])
        p_values[m] = p
        effect_sizes[m] = d

    summary = ExperimentSummary(
        skill=skill,
        platform=adapter.name,
        n_tasks=len(tasks),
        n_trials=n_trials,
        with_skill=with_agg,
        without_skill=without_agg,
        p_values=p_values,
        effect_sizes=effect_sizes,
    )
    tracker.log_summary(
        summary,
        skill_content_hash=skill_content_hash,
        skill_snapshot_dir=_skill_dir if _skill_dir.is_dir() else None,
    )
    return summary
