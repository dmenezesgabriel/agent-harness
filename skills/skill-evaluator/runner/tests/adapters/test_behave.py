import subprocess  # nosec B404
from pathlib import Path
from unittest.mock import Mock

import pytest

from runner.adapters.behave import (
    BehaveStructuralRunner,
    _as_object_list,
    _scenario_failure,
    _scenario_status,
)
from runner.models import ScenarioResult


def test_as_object_list_filters_non_mapping_values() -> None:
    # Arrange
    values: object = [{"name": "feature"}, "not-a-mapping", 3]

    # Act
    object_list = _as_object_list(values)

    # Assert
    assert object_list == [{"name": "feature"}]


def test_scenario_status_returns_failed_when_any_step_fails() -> None:
    # Arrange
    scenario: dict[str, object] = {
        "steps": [{"result": {"status": "passed"}}, {"result": {"status": "failed"}}]
    }

    # Act
    status = _scenario_status(scenario)

    # Assert
    assert status == "failed"


def test_scenario_failure_returns_first_failed_step_message() -> None:
    # Arrange
    scenario: dict[str, object] = {
        "steps": [{"result": {"status": "failed", "error_message": "bad chart"}}]
    }

    # Act
    failure = _scenario_failure(scenario)

    # Assert
    assert failure == "bad chart"


def test_read_results_ignores_background_and_keeps_failure(tmp_path: Path) -> None:
    # Arrange
    result_file = tmp_path / "results.json"
    result_file.write_text(
        """
        [{"name":"Chart rules","elements":[
          {"type":"background","name":"setup"},
          {"type":"scenario","name":"fails","steps":[{"result":{"status":"failed","error_message":"bad"}}]}
        ]}]
        """,
        encoding="utf-8",
    )
    proc = subprocess.CompletedProcess(
        args=["behave"], returncode=0, stdout="", stderr=""
    )

    # Act
    results = BehaveStructuralRunner().read_results(result_file, proc, tag="golden")

    # Assert
    assert results == [
        ScenarioResult(
            feature="Chart rules", scenario="fails", status="failed", failure="bad"
        )
    ]


def test_read_results_reports_json_decode_failure(tmp_path: Path) -> None:
    # Arrange
    result_file = tmp_path / "results.json"
    result_file.write_text("not-json", encoding="utf-8")
    proc = subprocess.CompletedProcess(
        args=["behave"], returncode=1, stdout="stdout failure", stderr=""
    )

    # Act
    results = BehaveStructuralRunner().read_results(result_file, proc, tag="generated")

    # Assert
    assert results == [
        ScenarioResult(
            feature="unknown",
            scenario="behave (generated)",
            status="failed",
            failure="stdout failure",
        )
    ]


def test_run_skips_generated_pass_when_artifacts_dir_is_static(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    evals_dir = tmp_path / "evals"
    fixtures_dir = evals_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)
    runner = BehaveStructuralRunner()
    expected_results = [ScenarioResult(feature="f", scenario="golden", status="passed")]
    behave_pass = Mock(return_value=expected_results)
    monkeypatch.setattr(runner, "_behave_pass", behave_pass)

    # Act
    results = runner.run(evals_dir, fixtures_dir)

    # Assert
    behave_pass.assert_called_once_with(evals_dir, fixtures_dir, tag="golden")
    assert results == expected_results
