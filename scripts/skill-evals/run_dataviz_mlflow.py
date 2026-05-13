#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["mlflow>=2.14,<3"]
# ///
"""Run the dataviz skill evals, split trigger/output reports, and log to MLflow.

Usage:
  uv run scripts/skill-evals/run_dataviz_mlflow.py \
    --manifest skills/dataviz/evals/evals.json \
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
REPORT = REPO_ROOT / "scripts" / "skill-evals" / "report.py"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_label(value: Any) -> str:
    text = str(value).strip() or "missing"
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in text)


def validate_manifest(payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str], Counter[str]]:
    if not isinstance(payload, dict):
        raise ValueError("Manifest must be a JSON object with skill_name and evals")
    if payload.get("skill_name") != "dataviz":
        raise ValueError("Manifest skill_name must be 'dataviz'")

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
        kind = case.get("kind")
        if kind not in {"trigger", "output"}:
            raise ValueError(f"Unsupported or missing eval kind at index {index}: {kind!r}")
        split = sanitize_label(case.get("split", "missing"))
        kind_counts[str(kind)] += 1
        split_counts[split] += 1
        if kind == "trigger":
            trigger_cases.append(case)
        else:
            output_cases.append(case)

    return trigger_cases, output_cases, kind_counts, split_counts


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


def log_json_artifact(path: Path) -> None:
    mlflow.log_artifact(str(path))


def log_summary_metrics(prefix: str, summary: dict[str, Any], names: list[str]) -> None:
    for name in names:
        value = summary.get(name)
        if isinstance(value, (int, float)):
            mlflow.log_metric(f"{prefix}_{name}", float(value))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Dataviz eval manifest")
    parser.add_argument("--trigger-runs", type=Path, required=True, help="Trigger run results keyed by eval id")
    parser.add_argument("--outputs", type=Path, required=True, help="Output results keyed by eval id")
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Root directory for file assertions; defaults to the dataviz evals directory",
    )
    parser.add_argument("--tracking-uri", default="file:./mlruns", help="MLflow tracking URI")
    parser.add_argument("--experiment-name", default="dataviz-evals", help="MLflow experiment name")
    parser.add_argument("--run-name", default="dataviz-skill-eval", help="MLflow run name")
    args = parser.parse_args()

    manifest = args.manifest.expanduser().resolve()
    trigger_runs = args.trigger_runs.expanduser().resolve()
    outputs = args.outputs.expanduser().resolve()
    artifact_root = (args.artifact_root.expanduser().resolve() if args.artifact_root else manifest.parent.resolve())

    for path in (manifest, trigger_runs, outputs):
        if not path.exists():
            raise FileNotFoundError(path)

    manifest_payload = read_json(manifest)
    trigger_cases, output_cases, kind_counts, split_counts = validate_manifest(manifest_payload)
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()

    trigger_manifest = {"skill_name": "dataviz", "evals": trigger_cases}
    output_manifest = {"skill_name": "dataviz", "evals": output_cases}

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment_name)

    benchmark_summary: dict[str, Any] = {}
    with mlflow.start_run(run_name=args.run_name):
        mlflow.log_params(
            {
                "manifest": str(manifest),
                "manifest_sha256": manifest_sha256,
                "trigger_runs": str(trigger_runs),
                "outputs": str(outputs),
                "artifact_root": str(artifact_root),
                "trigger_eval_count": str(len(trigger_cases)),
                "output_eval_count": str(len(output_cases)),
                "tracking_uri": args.tracking_uri,
            }
        )
        for kind, count in sorted(kind_counts.items()):
            mlflow.log_param(f"kind_{sanitize_label(kind)}_count", str(count))
        for split, count in sorted(split_counts.items()):
            mlflow.log_param(f"split_{sanitize_label(split)}_count", str(count))

        mlflow.log_artifact(str(manifest), artifact_path="inputs")
        mlflow.log_artifact(str(trigger_runs), artifact_path="inputs")
        mlflow.log_artifact(str(outputs), artifact_path="inputs")

        with tempfile.TemporaryDirectory(prefix="dataviz-evals-") as temp_dir:
            temp_path = Path(temp_dir)
            trigger_manifest_path = temp_path / "trigger_manifest.json"
            output_manifest_path = temp_path / "output_manifest.json"
            trigger_report_path = temp_path / "trigger_report.json"
            output_report_path = temp_path / "output_report.json"
            benchmark_summary_path = temp_path / "benchmark_summary.json"

            write_json(trigger_manifest_path, trigger_manifest)
            write_json(output_manifest_path, output_manifest)

            run_uv(
                SCORE_TRIGGERS,
                [
                    "--manifest",
                    str(trigger_manifest_path),
                    "--runs",
                    str(trigger_runs),
                    "--skill-dir",
                    str(manifest.parent.parent),
                    "--output",
                    str(trigger_report_path),
                ],
            )
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
            run_uv(
                REPORT,
                ["--inputs", str(trigger_report_path), str(output_report_path), "--output", str(benchmark_summary_path)],
            )

            trigger_report = read_json(trigger_report_path)
            output_report = read_json(output_report_path)
            benchmark_summary = read_json(benchmark_summary_path)

            trigger_summary = trigger_report.get("summary", {}) if isinstance(trigger_report, dict) else {}
            output_summary = output_report.get("summary", {}) if isinstance(output_report, dict) else {}
            benchmark_aggregate = (
                benchmark_summary.get("aggregate", {}) if isinstance(benchmark_summary, dict) else {}
            )

            log_summary_metrics("trigger", trigger_summary, ["precision", "recall", "f1", "accuracy"])
            log_summary_metrics("output", output_summary, ["pass_rate"])
            log_summary_metrics("benchmark", benchmark_aggregate, ["pass_rate"])

            log_json_artifact(trigger_manifest_path)
            log_json_artifact(output_manifest_path)
            log_json_artifact(trigger_report_path)
            log_json_artifact(output_report_path)
            log_json_artifact(benchmark_summary_path)

    print(json.dumps(benchmark_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
