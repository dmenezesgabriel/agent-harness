"""MLflow tracking integration.

Each experiment = one (skill, platform) combination.
Each run = one task_id.

Tags capture the full experimental cell for faceted SQL queries:
  skill, platform, task_id, complexity, language
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow

from harness.models import Finding, RunSummary, Task, TaskResult
from harness.tracking.base import Tracker
from harness.tracking.findings import log_finding as _log_finding

_MLRUNS_DIR = str(Path(__file__).parent.parent.parent / "mlruns")


def _experiment_name(skill: str, platform: str) -> str:
    return f"{skill}__{platform}"


class MLflowTracker(Tracker):
    def __init__(self, tracking_uri: str | None = None):
        uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI", f"file://{_MLRUNS_DIR}")
        mlflow.set_tracking_uri(uri)

    def log_result(self, result: TaskResult, task: Task, skill_dir: str | None = None, skill_content_hash: str | None = None) -> str:
        """Log one task result. Returns the run_id."""
        exp_name = _experiment_name(result.skill, result.platform)
        mlflow.set_experiment(exp_name)

        with mlflow.start_run(run_name=result.task_id) as run:
            tags = {
                "skill": result.skill,
                "platform": result.platform,
                "task_id": result.task_id,
                "task_title": task.title,
                "complexity": task.complexity,
                "language": task.language,
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

    def log_summary(self, summary: RunSummary, skill_content_hash: str | None = None, skill_snapshot_dir: Path | None = None) -> None:
        """Log aggregated run summary as a separate MLflow run."""
        exp_name = _experiment_name(summary.skill, summary.platform)
        mlflow.set_experiment(exp_name)

        with mlflow.start_run(run_name=f"__summary__n{summary.n_tasks}"):
            mlflow.set_tags({
                "skill": summary.skill,
                "platform": summary.platform,
                "run_type": "summary",
                "n_tasks": str(summary.n_tasks),
            })
            if skill_content_hash:
                mlflow.set_tag("skill_content_hash", skill_content_hash)
            for metric_name, (mean, std) in summary.metrics.items():
                mlflow.log_metric(f"metrics__{metric_name}__mean", mean)
                mlflow.log_metric(f"metrics__{metric_name}__std", std)
            if skill_snapshot_dir and skill_snapshot_dir.is_dir():
                mlflow.log_artifacts(str(skill_snapshot_dir), artifact_path="skill_snapshot")

    def log_finding(self, finding: Finding) -> None:
        _log_finding(
            finding.category,
            finding.message,
            run_id=finding.run_id,
            append_note=finding.append_note,
        )
