"""Tests for Tracker ABC, NullTracker, MLflowTracker, and BenchmarkRunner DI.

Covers: UT-001 through UT-005, IT-001, IT-002, OT-001 from issues 026 and 035.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.models import Finding, GoldStandard, RunSummary, Task, TaskResult
from harness.tracking.base import Tracker
from harness.tracking.null_tracker import NullTracker
from harness.tracking.tracker import MLflowTracker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def result() -> TaskResult:
    return TaskResult(
        task_id="test-001",
        skill="plan-it",
        platform="pi-agent",
        raw_output="output",
        latency_ms=100.0,
        input_tokens=50,
        output_tokens=30,
    )


@pytest.fixture
def task() -> Task:
    return Task(
        id="test-001",
        skill="plan-it",
        title="Test Task",
        instruction="Do something",
        evaluator="plan",
    )


@pytest.fixture
def summary() -> RunSummary:
    return RunSummary(
        skill="plan-it",
        platform="pi-agent",
        n_tasks=1,
    )


# ---------------------------------------------------------------------------
# UT-001 (035): TaskResult.total_tokens returns input_tokens + output_tokens
# ---------------------------------------------------------------------------

def test_task_result_total_tokens():
    r = TaskResult(
        task_id="t-001",
        skill="plan-it",
        platform="claude-code",
        raw_output="",
        latency_ms=0.0,
        input_tokens=40,
        output_tokens=20,
    )
    assert r.total_tokens == 60


# ---------------------------------------------------------------------------
# UT-002 (035): RunSummary field access — expected fields present, old ones absent
# ---------------------------------------------------------------------------

def test_run_summary_field_access():
    s = RunSummary(
        skill="plan-it",
        platform="pi-agent",
        n_tasks=3,
        metrics={"accuracy": (0.9, 0.1)},
    )
    assert s.skill == "plan-it"
    assert s.platform == "pi-agent"
    assert s.n_tasks == 3
    assert s.metrics["accuracy"] == (0.9, 0.1)
    assert not hasattr(s, "without_skill")
    assert not hasattr(s, "p_values")
    assert not hasattr(s, "trial_stats")
    assert not hasattr(s, "n_trials")


# ---------------------------------------------------------------------------
# UT-003 (035): GoldStandard default fields unchanged
# ---------------------------------------------------------------------------

def test_gold_standard_defaults():
    gs = GoldStandard()
    assert gs.required_sections == []
    assert gs.required_findings == []
    assert gs.test_commands == []
    assert gs.rubric == {}


# ---------------------------------------------------------------------------
# UT-001 (026): NullTracker.log_result does not raise
# ---------------------------------------------------------------------------

def test_null_tracker_log_result_does_not_raise(result, task, capsys):
    tracker = NullTracker()
    ret = tracker.log_result(result, task)
    assert ret == ""


# ---------------------------------------------------------------------------
# UT-002 (026): NullTracker.log_summary does not raise
# ---------------------------------------------------------------------------

def test_null_tracker_log_summary_does_not_raise(summary, capsys):
    tracker = NullTracker()
    tracker.log_summary(summary)


# ---------------------------------------------------------------------------
# UT-004 (026): MLflowTracker is an instance of Tracker
# ---------------------------------------------------------------------------

def test_mlflow_tracker_isinstance_tracker():
    assert issubclass(MLflowTracker, Tracker)


# ---------------------------------------------------------------------------
# UT-005 (026): NullTracker has no mlflow import
# ---------------------------------------------------------------------------

def test_null_tracker_has_no_mlflow_import():
    import harness.tracking.null_tracker as null_mod
    source_path = null_mod.__file__
    assert source_path is not None
    source = Path(source_path).read_text()
    assert "mlflow" not in source


# ---------------------------------------------------------------------------
# OBS-001 / OT-001 (026): NullTracker writes warning to stderr on construction
# ---------------------------------------------------------------------------

def test_null_tracker_warning_on_stderr(capsys):
    NullTracker()
    captured = capsys.readouterr()
    assert "[tracker] dry-run mode: experiment tracking is disabled" in captured.err


# ---------------------------------------------------------------------------
# IT-001 (026): BenchmarkRunner with NullTracker returns RunSummary
# ---------------------------------------------------------------------------

def test_benchmark_runner_with_null_tracker(tmp_path, result, task, summary):
    """Runner returns RunSummary when given a NullTracker; no MLflow calls."""
    from harness.runner import BenchmarkRunner

    null_tracker = NullTracker()

    fake_adapter = MagicMock()
    fake_adapter.name = "fake-platform"
    fake_adapter.run.return_value = result

    fake_evaluator = MagicMock()
    fake_evaluator.evaluate.side_effect = lambda r, t: r

    skill_dir = tmp_path / "plan-it"
    skill_dir.mkdir()
    import json
    task_data = {
        "id": "test-001",
        "skill": "plan-it",
        "title": "Test Task",
        "instruction": "Do something",
        "evaluator": "plan",
    }
    (skill_dir / "test-001.json").write_text(json.dumps(task_data))

    runner = BenchmarkRunner(tracker=null_tracker)

    mock_behave = MagicMock()
    mock_behave.evaluate.side_effect = lambda r, t: r
    mock_registry = MagicMock()
    mock_registry.resolve.side_effect = lambda name: (
        mock_behave if name == "behave" else fake_evaluator
    )
    with patch("harness.runner.evaluator_registry", mock_registry):
        result_summary = runner.run_experiment(
            adapter=fake_adapter,
            skill="plan-it",
            tasks_dir=tmp_path,
        )

    assert isinstance(result_summary, RunSummary)
    assert result_summary.skill == "plan-it"
    assert result_summary.n_tasks == 1


# ---------------------------------------------------------------------------
# IT-002 (035): NullTracker.log_result returns "" and writes warning to stderr
# ---------------------------------------------------------------------------

def test_null_tracker_log_result_returns_empty_string(result, task, capsys):
    tracker = NullTracker()
    ret = tracker.log_result(result, task)
    assert ret == ""
    captured = capsys.readouterr()
    assert "[tracker] dry-run mode: experiment tracking is disabled" in captured.err


# ---------------------------------------------------------------------------
# UT-003 (026): NullTracker.log_finding does not raise
# ---------------------------------------------------------------------------

def test_null_tracker_log_finding_does_not_raise(capsys):
    finding = Finding(category="timeout", message="Agent did not respond after 60s")
    tracker = NullTracker()
    tracker.log_finding(finding)


# ---------------------------------------------------------------------------
# OT-001 (035): MLflowTracker.log_result run name equals task_id
# ---------------------------------------------------------------------------

def test_mlflow_tracker_log_result_run_name_is_task_id(result, task):
    """OT-001: MLflow run name is task_id with no condition or trial suffix."""
    with patch("mlflow.set_tracking_uri"), \
         patch("mlflow.set_experiment"), \
         patch("mlflow.set_tags"), \
         patch("mlflow.log_metrics"), \
         patch("mlflow.log_text"), \
         patch("mlflow.start_run") as mock_start_run:

        mock_run = MagicMock()
        mock_run.__enter__ = MagicMock(return_value=mock_run)
        mock_run.__exit__ = MagicMock(return_value=False)
        mock_run.info.run_id = "fake-run-id"
        mock_start_run.return_value = mock_run

        tracker = MLflowTracker(tracking_uri="file:///tmp/mlruns-test")
        tracker.log_result(result, task)

    mock_start_run.assert_called_once_with(run_name=result.task_id)


# ---------------------------------------------------------------------------
# OT-001 (026): bench-run --dry-run emits warning via CLI path
# ---------------------------------------------------------------------------

def test_dry_run_cli_uses_null_tracker_and_warns(tmp_path):
    """OT-001: invoking the CLI with --dry-run wires NullTracker and warning appears."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from run import main
    from click.testing import CliRunner

    (tmp_path / "plan-it").mkdir()

    captured = {}

    def fake_run_experiment(**kwargs):
        captured["tracker"] = kwargs.get("tracker")
        return RunSummary(skill="plan-it", platform="pi-agent", n_tasks=0)

    with (
        patch("run._TASKS_DIR", tmp_path),
        patch("run._make_adapter", return_value=MagicMock()),
        patch("run.run_experiment", side_effect=fake_run_experiment),
        patch("run._print_summary"),
    ):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--skill", "plan-it",
            "--platform", "pi-agent",
            "--dry-run",
        ])

    assert result.exit_code == 0, result.output
    assert isinstance(captured.get("tracker"), NullTracker)
    assert "[tracker] dry-run mode: experiment tracking is disabled" in result.output


# ---------------------------------------------------------------------------
# UT-001 (036): Task.from_dict with no "evaluators" key falls back to [evaluator]
# ---------------------------------------------------------------------------

def test_task_from_dict_no_evaluators_key_falls_back_to_evaluator():
    """UT-001: evaluators defaults to [task.evaluator] when key absent from JSON."""
    from harness.models import Task
    t = Task.from_dict({
        "id": "t-001",
        "skill": "plan-it",
        "title": "Test",
        "instruction": "Do X",
        "evaluator": "plan",
    })
    assert t.evaluators == ["plan"]


# ---------------------------------------------------------------------------
# UT-002 (036): Task.from_dict with explicit "evaluators" key parses correctly
# ---------------------------------------------------------------------------

def test_task_from_dict_with_explicit_evaluators_key():
    """UT-002: explicit evaluators list is preserved as-is."""
    from harness.models import Task
    t = Task.from_dict({
        "id": "t-001",
        "skill": "plan-it",
        "title": "Test",
        "instruction": "Do X",
        "evaluator": "plan",
        "evaluators": ["plan", "behave"],
    })
    assert t.evaluators == ["plan", "behave"]


# ---------------------------------------------------------------------------
# IT-003 (036): BenchmarkRunner with NullTracker returns RunSummary with n_tasks == 1
# ---------------------------------------------------------------------------

def test_benchmark_runner_returns_run_summary_single_execution(tmp_path):
    """IT-003: run_experiment executes each task once and returns RunSummary with n_tasks == 1."""
    import json
    from unittest.mock import MagicMock, patch
    from harness.runner import BenchmarkRunner
    from harness.models import TaskResult

    null_tracker = NullTracker()

    fake_adapter = MagicMock()
    fake_adapter.name = "fake-platform"
    fake_adapter.run.return_value = TaskResult(
        task_id="t-001",
        skill="plan-it",
        platform="fake-platform",
        raw_output="output",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )

    fake_ev = MagicMock()
    fake_ev.evaluate.side_effect = lambda r, t: r

    skill_dir = tmp_path / "plan-it"
    skill_dir.mkdir()
    (skill_dir / "t-001.json").write_text(json.dumps({
        "id": "t-001",
        "skill": "plan-it",
        "title": "Test",
        "instruction": "Do X",
        "evaluator": "plan",
        "evaluators": ["plan"],
    }))

    mock_registry = MagicMock()
    mock_registry.resolve.return_value = fake_ev

    runner = BenchmarkRunner(tracker=null_tracker)
    with patch("harness.runner.evaluator_registry", mock_registry):
        summary = runner.run_experiment(
            adapter=fake_adapter,
            skill="plan-it",
            tasks_dir=tmp_path,
        )

    assert isinstance(summary, RunSummary)
    assert summary.n_tasks == 1
    fake_adapter.run.assert_called_once()


# ---------------------------------------------------------------------------
# IT-001 (038): CLI invokes run_experiment without removed parameters
# ---------------------------------------------------------------------------

def test_cli_invokes_run_experiment_without_removed_parameters(tmp_path):
    """IT-001: run.py forwards no n_trials, use_judge, or with_skill_only to run_experiment."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from run import main
    from click.testing import CliRunner

    (tmp_path / "plan-it").mkdir()

    captured_kwargs: dict = {}

    def fake_run_experiment(**kwargs):
        captured_kwargs.update(kwargs)
        return RunSummary(skill="plan-it", platform="pi-agent", n_tasks=0)

    mock_lint = MagicMock()
    mock_lint.return_value.validate.return_value.passed = True

    with (
        patch("run._TASKS_DIR", tmp_path),
        patch("run.SkillLintValidator", mock_lint),
        patch("run._make_adapter", return_value=MagicMock()),
        patch("run.run_experiment", side_effect=fake_run_experiment),
        patch("run._print_summary"),
    ):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--skill", "plan-it",
            "--platform", "pi-agent",
            "--dry-run",
        ])

    assert result.exit_code == 0, result.output
    assert "n_trials" not in captured_kwargs
    assert "use_judge" not in captured_kwargs
    assert "with_skill_only" not in captured_kwargs


# ---------------------------------------------------------------------------
# IT-002 (038): _print_summary renders RunSummary without comparison columns
# ---------------------------------------------------------------------------

def test_print_summary_renders_single_metric_table(tmp_path, capsys):
    """IT-002: _print_summary shows mean±std for each metric; no 'Without skill' or 'p-value'."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from run import _print_summary
    from io import StringIO
    from click.testing import CliRunner

    summary = RunSummary(
        skill="plan-it",
        platform="pi-agent",
        n_tasks=2,
        metrics={"behave_pass_rate": (0.85, 0.0), "accuracy": (1.0, 0.0)},
    )

    output = StringIO()
    from rich.console import Console
    import run as run_module
    original_console = run_module.console
    run_module.console = Console(file=output, highlight=False)
    try:
        _print_summary(summary, None)
    finally:
        run_module.console = original_console

    rendered = output.getvalue()
    assert "0.850" in rendered
    assert "Without skill" not in rendered
    assert "p-value" not in rendered
