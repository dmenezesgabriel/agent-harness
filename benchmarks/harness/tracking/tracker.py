"""MLflow tracking integration.

Each experiment = one (skill, platform) combination.
Each run = one (task_id, condition, trial_index) triple.

Tags capture the full experimental cell for faceted SQL queries:
  skill, platform, condition, task_id, complexity, language, trial
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow

from harness.models import ExperimentSummary, Task, TrialResult

_MLRUNS_DIR = str(Path(__file__).parent.parent.parent / "mlruns")


def _experiment_name(skill: str, platform: str) -> str:
    return f"{skill}__{platform}"


class MLflowTracker:
    def __init__(self, tracking_uri: str | None = None):
        uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", f"file://{_MLRUNS_DIR}")
        mlflow.set_tracking_uri(uri)

    def log_trial(self, result: TrialResult, task: Task, skill_dir: str | None = None, skill_content_hash: str | None = None) -> str:
        """Log one trial result. Returns the run_id."""
        exp_name = _experiment_name(result.skill, result.platform)
        mlflow.set_experiment(exp_name)

        with mlflow.start_run(run_name=f"{result.task_id}__{result.condition}__trial{result.trial_index}") as run:
            tags = {
                "skill": result.skill,
                "platform": result.platform,
                "condition": result.condition,
                "task_id": result.task_id,
                "task_title": task.title,
                "complexity": task.complexity,
                "language": task.language,
                "trial": str(result.trial_index),
                "evaluator": task.evaluator,
            }
            if skill_dir:
                tags["skill_variant"] = skill_dir
            if skill_content_hash:
                tags["skill_content_hash"] = skill_content_hash
            mlflow.set_tags(tags)
            mlflow.log_metrics({
                "accuracy": result.accuracy,
                "precision": result.precision,
                "recall": result.recall,
                "f1": result.f1,
                "quality_score": result.quality_score,
                "test_pass_rate": result.test_pass_rate,
                "behave_pass_rate": result.behave_pass_rate,
                "judge_score": result.judge_score,
                "latency_ms": result.latency_ms,
                "input_tokens": float(result.input_tokens),
                "output_tokens": float(result.output_tokens),
                "total_tokens": float(result.total_tokens),
            })
            # log artifacts
            mlflow.log_text(result.raw_output or "", "raw_output.txt")
            if result.evaluator_details:
                mlflow.log_text(
                    json.dumps(result.evaluator_details, indent=2),
                    "evaluator_details.json",
                )
            if result.behave_scenarios:
                mlflow.log_text(
                    json.dumps(result.behave_scenarios, indent=2),
                    "behave_scenarios.json",
                )
            if result.judge_verdict:
                mlflow.log_text(result.judge_verdict, "judge_verdict.txt")

            return run.info.run_id

    def log_summary(self, summary: ExperimentSummary, skill_content_hash: str | None = None, skill_snapshot_dir: Path | None = None) -> None:
        """Log aggregated experiment summary as a separate MLflow run."""
        exp_name = _experiment_name(summary.skill, summary.platform)
        mlflow.set_experiment(exp_name)

        with mlflow.start_run(run_name=f"__summary__n{summary.n_tasks}_t{summary.n_trials}"):
            mlflow.set_tags({
                "skill": summary.skill,
                "platform": summary.platform,
                "run_type": "summary",
                "n_tasks": str(summary.n_tasks),
                "n_trials": str(summary.n_trials),
            })
            if skill_content_hash:
                mlflow.set_tag("skill_content_hash", skill_content_hash)
            for metric_name, (mean, std) in summary.with_skill.items():
                mlflow.log_metric(f"with_skill__{metric_name}__mean", mean)
                mlflow.log_metric(f"with_skill__{metric_name}__std", std)
            for metric_name, (mean, std) in summary.without_skill.items():
                mlflow.log_metric(f"without_skill__{metric_name}__mean", mean)
                mlflow.log_metric(f"without_skill__{metric_name}__std", std)
            for metric_name, pval in summary.p_values.items():
                mlflow.log_metric(f"p_value__{metric_name}", pval)
            for metric_name, eff in summary.effect_sizes.items():
                mlflow.log_metric(f"effect_size__{metric_name}", eff)
            # behave summary
            for condition_label, agg in [("with_skill", summary.with_skill), ("without_skill", summary.without_skill)]:
                if "behave_pass_rate" in agg:
                    mean, std = agg["behave_pass_rate"]
                    mlflow.log_metric(f"{condition_label}__behave_pass_rate__mean", mean)
                    mlflow.log_metric(f"{condition_label}__behave_pass_rate__std", std)
            if skill_snapshot_dir and skill_snapshot_dir.is_dir():
                mlflow.log_artifacts(str(skill_snapshot_dir), artifact_path="skill_snapshot")
