import subprocess  # nosec B404
from pathlib import Path
from unittest.mock import Mock

import pytest

from runner.adapters.behave import (
    BehaveStructuralRunner,
    _as_object_list,
    _feature_scope_error,
    _scenario_failure,
    _scenario_status,
)
from runner.models import ScenarioResult


class TestHelpers:
    def test_as_object_list_filters_non_mapping_values(self) -> None:
        # Arrange
        values: object = [{"name": "feature"}, "not-a-mapping", 3]

        # Act
        object_list = _as_object_list(values)

        # Assert
        assert object_list == [{"name": "feature"}]

    def test_scenario_status_returns_failed_when_any_step_fails(self) -> None:
        # Arrange
        scenario: dict[str, object] = {
            "steps": [
                {"result": {"status": "passed"}},
                {"result": {"status": "failed"}},
            ]
        }

        # Act
        status = _scenario_status(scenario)

        # Assert
        assert status == "failed"

    def test_scenario_failure_returns_first_failed_step_message(self) -> None:
        # Arrange
        scenario: dict[str, object] = {
            "steps": [{"result": {"status": "failed", "error_message": "bad chart"}}]
        }

        # Act
        failure = _scenario_failure(scenario)

        # Assert
        assert failure == "bad chart"


class TestBehaveStructuralRunner:
    def test_feature_scope_error_flags_mixed_feature_tags(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        (evals_dir / "mixed.feature").write_text(
            "@golden @generated\nFeature: mixed scope\n",
            encoding="utf-8",
        )

        result = _feature_scope_error(evals_dir)

        assert result is not None
        assert result.status == "failed"
        assert "WARNING: evaluation process" in str(result.failure)
        assert "tagged with both @golden and @generated" in str(result.failure)

    def test_feature_scope_error_allows_scenario_level_scope_tags(
        self, tmp_path: Path
    ) -> None:
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        (evals_dir / "separated.feature").write_text(
            "@implement_it\n"
            "Feature: separated scope\n\n"
            "  @golden\n"
            "  Scenario: golden check\n"
            "    Then ok\n\n"
            "  @generated\n"
            "  Scenario: generated check\n"
            "    Then ok\n",
            encoding="utf-8",
        )

        assert _feature_scope_error(evals_dir) is None

    def test_read_results_ignores_background_and_keeps_failure(
        self, tmp_path: Path
    ) -> None:
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

    def test_read_results_reports_json_decode_failure(self, tmp_path: Path) -> None:
        # Arrange
        result_file = tmp_path / "results.json"
        result_file.write_text("not-json", encoding="utf-8")
        proc = subprocess.CompletedProcess(
            args=["behave"], returncode=1, stdout="stdout failure", stderr=""
        )

        # Act
        results = BehaveStructuralRunner().read_results(
            result_file, proc, tag="generated"
        )

        # Assert
        assert results == [
            ScenarioResult(
                feature="unknown",
                scenario="behave (generated)",
                status="failed",
                failure="stdout failure",
            )
        ]

    def test_run_skips_generated_pass_when_artifacts_dir_is_golden(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "evals"
        golden_dir = evals_dir / "fixtures" / "golden"
        golden_dir.mkdir(parents=True)
        runner = BehaveStructuralRunner()
        expected_results = [
            ScenarioResult(feature="f", scenario="golden", status="passed")
        ]
        behave_pass = Mock(return_value=expected_results)
        monkeypatch.setattr(runner, "_behave_pass", behave_pass)

        # Act
        results = runner.run(evals_dir, golden_dir)

        # Assert
        behave_pass.assert_called_once_with(evals_dir, golden_dir, tag="golden")
        assert results == expected_results

    def test_run_checks_each_input_artifact_dir_independently(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "evals"
        golden_dir = evals_dir / "fixtures" / "golden"
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        input_a_dir = generated_dir / "input_a"
        input_b_dir = generated_dir / "input_b"
        golden_dir.mkdir(parents=True)
        input_a_dir.mkdir(parents=True)
        input_b_dir.mkdir(parents=True)
        runner = BehaveStructuralRunner()

        def behave_pass(
            _evals_dir: Path, artifacts_dir: Path, tag: str
        ) -> list[ScenarioResult]:
            del tag
            return [
                ScenarioResult(
                    feature="generated output",
                    scenario=f"has artifact in {artifacts_dir.name}",
                    status="passed",
                )
            ]

        behave_pass_mock = Mock(side_effect=behave_pass)
        monkeypatch.setattr(runner, "_behave_pass", behave_pass_mock)

        # Act
        results = runner.run(evals_dir, generated_dir)

        # Assert
        assert behave_pass_mock.call_count == 3
        assert results == [
            ScenarioResult(
                feature="generated output",
                scenario="has artifact in golden",
                status="passed",
            ),
            ScenarioResult(
                feature="generated output",
                scenario="input_a: has artifact in input_a",
                status="passed",
            ),
            ScenarioResult(
                feature="generated output",
                scenario="input_b: has artifact in input_b",
                status="passed",
            ),
        ]

    def test_run_uses_aggregate_generated_dir_without_input_subdirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "evals"
        golden_dir = evals_dir / "fixtures" / "golden"
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        golden_dir.mkdir(parents=True)
        (generated_dir / "src").mkdir(parents=True)
        runner = BehaveStructuralRunner()
        behave_pass = Mock(return_value=[])
        monkeypatch.setattr(runner, "_behave_pass", behave_pass)

        # Act
        runner.run(evals_dir, generated_dir)

        # Assert
        assert behave_pass.call_args_list[1].args == (evals_dir, generated_dir)
