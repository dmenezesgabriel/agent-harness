"""Smoke tests for bench-promote and bench-compare against a temp MLflow backend."""
import tempfile
from pathlib import Path

import mlflow
import pytest
from click.testing import CliRunner

# champion module is at benchmarks/champion.py — sys.path set by conftest.py
from champion import compare, promote


@pytest.fixture
def mlflow_backend(tmp_path):
    """Temp MLflow file backend with two synthetic summary runs."""
    uri = f"file://{tmp_path}/mlruns"
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment("plan-it__pi-agent")

    # run A
    with mlflow.start_run(run_name="__summary__n5") as run_a:
        mlflow.set_tags({
            "run_type": "summary", "skill": "plan-it", "platform": "pi-agent",
            "n_tasks": "5",
            "skill_content_hash": "sha256:aaaa000000000000",
        })
        mlflow.log_metrics({"metrics__f1__mean": 0.8, "metrics__behave_pass_rate__mean": 0.9,
                            "metrics__quality_score__mean": 7.0, "metrics__latency_ms__mean": 1200.0})
        run_a_id = run_a.info.run_id

    # run B
    with mlflow.start_run(run_name="__summary__n5") as run_b:
        mlflow.set_tags({
            "run_type": "summary", "skill": "plan-it", "platform": "pi-agent",
            "n_tasks": "5",
            "skill_content_hash": "sha256:bbbb000000000000",
        })
        mlflow.log_metrics({"metrics__f1__mean": 0.7, "metrics__behave_pass_rate__mean": 0.8,
                            "metrics__quality_score__mean": 6.5, "metrics__latency_ms__mean": 1100.0})
        run_b_id = run_b.info.run_id

    yield {"uri": uri, "run_a_id": run_a_id, "run_b_id": run_b_id}
    mlflow.set_tracking_uri("")  # reset


def test_promote_sets_champion_tag(mlflow_backend):
    """SMK-001: promoting hash-A sets champion=true on run A, not run B."""
    runner = CliRunner()
    result = runner.invoke(promote, [
        "--skill", "plan-it",
        "--content-hash", "sha256:aaaa000000000000",
        "--tracking-uri", mlflow_backend["uri"],
    ])
    assert result.exit_code == 0, result.output

    client = mlflow.MlflowClient()
    run_a = client.get_run(mlflow_backend["run_a_id"])
    run_b = client.get_run(mlflow_backend["run_b_id"])
    assert run_a.data.tags.get("champion") == "true"
    assert "champion" not in run_b.data.tags


def test_compare_shows_champion_row(mlflow_backend):
    """SMK-002: bench-compare shows ★ champion after promotion."""
    runner = CliRunner(env={"COLUMNS": "200"})
    # promote A first
    runner.invoke(promote, [
        "--skill", "plan-it",
        "--content-hash", "sha256:aaaa000000000000",
        "--tracking-uri", mlflow_backend["uri"],
    ])
    result = runner.invoke(compare, [
        "--skill", "plan-it",
        "--tracking-uri", mlflow_backend["uri"],
    ])
    assert result.exit_code == 0, result.output
    assert "champion" in result.output
    assert "aaaa" in result.output


def test_promote_unknown_hash_exits_nonzero(mlflow_backend):
    """SMK-003: unknown hash → exit code 1."""
    runner = CliRunner()
    result = runner.invoke(promote, [
        "--skill", "plan-it",
        "--content-hash", "sha256:ffffffffffffffff",
        "--tracking-uri", mlflow_backend["uri"],
    ])
    assert result.exit_code == 1
    assert "sha256:ffffffffffffffff" in result.output or "No summary run" in result.output


def test_promote_is_idempotent(mlflow_backend):
    """NFR-002: promoting the same hash twice leaves exactly one champion."""
    runner = CliRunner()
    for _ in range(2):
        runner.invoke(promote, [
            "--skill", "plan-it",
            "--content-hash", "sha256:aaaa000000000000",
            "--tracking-uri", mlflow_backend["uri"],
        ])
    client = mlflow.MlflowClient()
    run_a = client.get_run(mlflow_backend["run_a_id"])
    run_b = client.get_run(mlflow_backend["run_b_id"])
    assert run_a.data.tags.get("champion") == "true"
    assert "champion" not in run_b.data.tags


def test_compare_no_champion_shows_hint(mlflow_backend):
    """AC-005: no champion set → output includes promote hint."""
    runner = CliRunner()
    result = runner.invoke(compare, [
        "--skill", "plan-it",
        "--tracking-uri", mlflow_backend["uri"],
    ])
    assert result.exit_code == 0
    assert "bench-promote" in result.output
