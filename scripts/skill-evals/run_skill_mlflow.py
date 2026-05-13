#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["mlflow>=2.14,<3"]
# ///
"""Run skill evals, split trigger/output reports, and log results to MLflow.

Usage:
  uv run scripts/skill-evals/run_skill_mlflow.py \
    --manifest skills/software-feature-planning/evals/evals.json \
    --trigger-runs runs/triggers.json \
    --outputs runs/outputs.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import mlflow

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORE_TRIGGERS = REPO_ROOT / "scripts" / "skill-evals" / "score_triggers.py"
SCORE_OUTPUTS = REPO_ROOT / "scripts" / "skill-evals" / "score_outputs.py"
SEMANTIC_SCORE = REPO_ROOT / "scripts" / "skill-evals" / "semantic_score.py"
REPORT = REPO_ROOT / "scripts" / "skill-evals" / "report.py"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_label(value: Any) -> str:
    text = str(value).strip() or "missing"
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in text)


def validate_manifest(payload: Any) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], Counter[str], Counter[str]]:
    if not isinstance(payload, dict):
        raise ValueError("Manifest must be a JSON object with skill_name and evals")
    skill_name = str(payload.get("skill_name", "")).strip()
    if not skill_name:
        raise ValueError("Manifest must include a non-empty 'skill_name'")

    evals = payload.get("evals")
    if not isinstance(evals, list):
        raise ValueError("Manifest must include an 'evals' array")

    trigger_cases: list[dict[str, Any]] = []
    output_cases: list[dict[str, Any]] = []
    kind_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()

    for index, case in enumerate(evals):
        if not isinstance(case, dict):
            raise ValueError(f"Manifest eval at index {index} must be an object")
        kind = str(case.get("kind", "")).strip()
        if kind not in {"trigger", "output"}:
            raise ValueError(f"Unsupported or missing eval kind at index {index}: {kind!r}")
        split = sanitize_label(case.get("split", "missing"))
        kind_counts[kind] += 1
        split_counts[split] += 1
        if kind == "trigger":
            trigger_cases.append(case)
        else:
            output_cases.append(case)

    return skill_name, trigger_cases, output_cases, kind_counts, split_counts


def run_uv(script: Path, args: list[str]) -> None:
    command = ["uv", "run", str(script), *args]
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed with exit code {result.returncode}\n"
            f"command: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def log_json_artifact(path: Path, artifact_path: str | None = None) -> None:
    if artifact_path:
        mlflow.log_artifact(str(path), artifact_path=artifact_path)
    else:
        mlflow.log_artifact(str(path))


def log_summary_metrics(prefix: str, summary: dict[str, Any], names: list[str]) -> None:
    for name in names:
        value = summary.get(name)
        if isinstance(value, (int, float)):
            mlflow.log_metric(f"{prefix}_{name}", float(value))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Skill eval manifest")
    parser.add_argument("--trigger-runs", type=Path, help="Trigger run results keyed by eval id")
    parser.add_argument("--outputs", type=Path, help="Output results keyed by eval id")
    parser.add_argument("--skill-dir", type=Path, help="Skill directory; defaults to manifest parent")
    parser.add_argument("--artifact-root", type=Path, help="Root directory for file assertions; defaults to the evals directory")
    parser.add_argument("--variant", type=Path, help="Optional generated variant SKILL.md to log alongside the run")
    parser.add_argument("--semantic-model", help="Optional SentenceTransformer model for routing diagnostics")
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"), help="Root skills directory for semantic routing candidates")
    parser.add_argument("--semantic-top-k", type=int, default=3, help="Top-k route hit threshold for semantic diagnostics")
    parser.add_argument("--cluster-failures", action="store_true", help="Cluster failed prompts in semantic diagnostics")
    parser.add_argument("--semantic-max-clusters", type=int, default=5, help="Maximum number of semantic failure clusters")
    parser.add_argument("--tracking-uri", default="file:./mlruns", help="MLflow tracking URI")
    parser.add_argument("--experiment-name", default="skill-evals", help="MLflow experiment name")
    parser.add_argument("--run-name", help="MLflow run name; defaults to <skill_name>-skill-eval")
    args = parser.parse_args()

    manifest = args.manifest.expanduser().resolve()
    if not manifest.exists():
        raise FileNotFoundError(manifest)

    manifest_payload = read_json(manifest)
    skill_name, trigger_cases, output_cases, kind_counts, split_counts = validate_manifest(manifest_payload)

    skill_dir = (args.skill_dir.expanduser().resolve() if args.skill_dir else manifest.parent.parent.resolve())
    artifact_root = (args.artifact_root.expanduser().resolve() if args.artifact_root else manifest.parent.resolve())
    variant = args.variant.expanduser().resolve() if args.variant else None
    if variant is not None and not variant.exists():
        raise FileNotFoundError(variant)

    trigger_runs = args.trigger_runs.expanduser().resolve() if args.trigger_runs else None
    outputs = args.outputs.expanduser().resolve() if args.outputs else None
    if trigger_cases and trigger_runs is None:
        raise ValueError("Manifest includes trigger evals but --trigger-runs was not provided")
    if output_cases and outputs is None:
        raise ValueError("Manifest includes output evals but --outputs was not provided")
    for path in (trigger_runs, outputs):
        if path is not None and not path.exists():
            raise FileNotFoundError(path)

    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    run_name = args.run_name or f"{skill_name}-skill-eval"

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment_name)

    benchmark_summary: dict[str, Any] = {}
    with mlflow.start_run(run_name=run_name):
        params = {
            "skill_name": skill_name,
            "manifest": str(manifest),
            "manifest_sha256": manifest_sha256,
            "skill_dir": str(skill_dir),
            "artifact_root": str(artifact_root),
            "trigger_eval_count": str(len(trigger_cases)),
            "output_eval_count": str(len(output_cases)),
            "tracking_uri": args.tracking_uri,
        }
        if trigger_runs is not None:
            params["trigger_runs"] = str(trigger_runs)
        if outputs is not None:
            params["outputs"] = str(outputs)
        if variant is not None:
            params["variant"] = str(variant)
            params["variant_sha256"] = hashlib.sha256(variant.read_bytes()).hexdigest()
        if args.semantic_model:
            params["semantic_model"] = args.semantic_model
            params["semantic_top_k"] = str(args.semantic_top_k)
            params["semantic_skills_dir"] = str(args.skills_dir.expanduser().resolve())
            params["semantic_cluster_failures"] = str(bool(args.cluster_failures))
        mlflow.log_params(params)
        for kind, count in sorted(kind_counts.items()):
            mlflow.log_param(f"kind_{sanitize_label(kind)}_count", str(count))
        for split, count in sorted(split_counts.items()):
            mlflow.log_param(f"split_{sanitize_label(split)}_count", str(count))

        log_json_artifact(manifest, artifact_path="inputs")
        if trigger_runs is not None:
            log_json_artifact(trigger_runs, artifact_path="inputs")
        if outputs is not None:
            log_json_artifact(outputs, artifact_path="inputs")
        if variant is not None:
            mlflow.log_artifact(str(variant), artifact_path="variant")

        report_paths: list[Path] = []
        with tempfile.TemporaryDirectory(prefix=f"{sanitize_label(skill_name)}-evals-") as temp_dir:
            temp_path = Path(temp_dir)

            if trigger_cases:
                trigger_manifest_path = temp_path / "trigger_manifest.json"
                trigger_report_path = temp_path / "trigger_report.json"
                write_json(trigger_manifest_path, {"skill_name": skill_name, "evals": trigger_cases})
                run_uv(
                    SCORE_TRIGGERS,
                    [
                        "--manifest",
                        str(trigger_manifest_path),
                        "--runs",
                        str(trigger_runs),
                        "--skill-dir",
                        str(skill_dir),
                        "--output",
                        str(trigger_report_path),
                    ],
                )
                report_paths.append(trigger_report_path)
                trigger_report = read_json(trigger_report_path)
                trigger_summary = trigger_report.get("summary", {}) if isinstance(trigger_report, dict) else {}
                log_summary_metrics(
                    "trigger",
                    trigger_summary,
                    [
                        "precision",
                        "recall",
                        "f1",
                        "accuracy",
                        "intent_accuracy",
                        "entity_precision",
                        "entity_recall",
                        "entity_f1",
                    ],
                )
                log_json_artifact(trigger_manifest_path)
                log_json_artifact(trigger_report_path)

            if output_cases:
                output_manifest_path = temp_path / "output_manifest.json"
                output_report_path = temp_path / "output_report.json"
                write_json(output_manifest_path, {"skill_name": skill_name, "evals": output_cases})
                run_uv(
                    SCORE_OUTPUTS,
                    [
                        "--manifest",
                        str(output_manifest_path),
                        "--outputs",
                        str(outputs),
                        "--artifact-root",
                        str(artifact_root),
                        "--output",
                        str(output_report_path),
                    ],
                )
                report_paths.append(output_report_path)
                output_report = read_json(output_report_path)
                output_summary = output_report.get("summary", {}) if isinstance(output_report, dict) else {}
                log_summary_metrics("output", output_summary, ["pass_rate"])
                log_json_artifact(output_manifest_path)
                log_json_artifact(output_report_path)

            if args.semantic_model and trigger_cases:
                semantic_report_path = temp_path / "semantic_report.json"
                semantic_args = [
                    "--manifest",
                    str(manifest),
                    "--runs",
                    str(trigger_runs),
                    "--skill-dir",
                    str(skill_dir),
                    "--skills-dir",
                    str(args.skills_dir.expanduser().resolve()),
                    "--model",
                    args.semantic_model,
                    "--top-k",
                    str(args.semantic_top_k),
                    "--max-clusters",
                    str(args.semantic_max_clusters),
                    "--output",
                    str(semantic_report_path),
                ]
                if args.cluster_failures:
                    semantic_args.append("--cluster-failures")
                run_uv(SEMANTIC_SCORE, semantic_args)
                semantic_report = read_json(semantic_report_path)
                semantic_summary = semantic_report.get("summary", {}) if isinstance(semantic_report, dict) else {}
                log_summary_metrics(
                    "semantic",
                    semantic_summary,
                    [
                        "positive_route_top1_accuracy",
                        f"positive_route_top{max(1, args.semantic_top_k)}_accuracy",
                        "positive_target_similarity_mean",
                        "negative_target_similarity_mean",
                        "positive_margin_mean",
                        "negative_margin_mean",
                    ],
                )
                log_json_artifact(semantic_report_path)

            if not report_paths:
                raise ValueError("No reports were generated")

            benchmark_summary_path = temp_path / "benchmark_summary.json"
            run_uv(REPORT, ["--inputs", *[str(path) for path in report_paths], "--output", str(benchmark_summary_path)])
            benchmark_summary = read_json(benchmark_summary_path)
            benchmark_aggregate = benchmark_summary.get("aggregate", {}) if isinstance(benchmark_summary, dict) else {}
            log_summary_metrics("benchmark", benchmark_aggregate, ["pass_rate"])
            log_json_artifact(benchmark_summary_path)

    print(json.dumps(benchmark_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
