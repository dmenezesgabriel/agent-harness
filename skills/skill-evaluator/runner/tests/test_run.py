import subprocess  # nosec B404
from pathlib import Path

import pytest
from pydantic import ValidationError

from runner.ports import ArtifactSet, JudgeVerdict
from runner.run import (
    JudgeReport,
    RubricFile,
    ScenarioResult,
    _as_object_list,
    _evaluate_skill,
    _extract_section,
    _find_primary_chart,
    _invoke_skill,
    _measure_artifacts,
    _read_behave_results,
    _run_behave,
    _run_judge,
    _scenario_failure,
    _scenario_status,
    _write_report,
)

_PASSING_SCORE = 0.9
_FAILING_SCORE = 0.2
_EXPECTED_REPORT_CHECKS = 3


class FakeAgentPort:
    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        return ArtifactSet(
            workdir=Path("run"), files={f"{skill_name}.js": f"new Chart(); {prompt}"}
        )


class FakeJudgePort:
    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeVerdict:
        return JudgeVerdict(
            rubric_id=rubric_id,
            passed="pass" in rubric,
            score=_PASSING_SCORE if "pass" in rubric else _FAILING_SCORE,
            reasoning=f"judged {artifact_content}",
        )


def test_rubric_file_requires_artifact_file_and_prompt() -> None:
    # Arrange
    raw_rubric_file = {"rubrics": [{"id": "missing_prompt"}]}

    # Act / Assert
    with pytest.raises(ValidationError):
        RubricFile.model_validate(raw_rubric_file)


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


def test_read_behave_results_ignores_background_and_keeps_failure(
    tmp_path: Path,
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
    results = _read_behave_results(result_file, proc, tag="golden")

    # Assert
    assert results == [
        ScenarioResult(
            feature="Chart rules", scenario="fails", status="failed", failure="bad"
        )
    ]


def test_read_behave_results_reports_json_decode_failure(tmp_path: Path) -> None:
    # Arrange
    result_file = tmp_path / "results.json"
    result_file.write_text("not-json", encoding="utf-8")
    proc = subprocess.CompletedProcess(
        args=["behave"], returncode=1, stdout="stdout failure", stderr=""
    )

    # Act
    results = _read_behave_results(result_file, proc, tag="live")

    # Assert
    assert results == [
        ScenarioResult(
            feature="unknown",
            scenario="behave (live)",
            status="failed",
            failure="stdout failure",
        )
    ]


def test_measure_artifacts_counts_text_files_relative_to_artifact_dir(
    tmp_path: Path,
) -> None:
    # Arrange
    chart_dir = tmp_path / "charts"
    chart_dir.mkdir()
    (chart_dir / "main.js").write_text("chart", encoding="utf-8")

    # Act
    sizes = _measure_artifacts(tmp_path)

    # Assert
    assert sizes == {"charts/main.js": len("chart")}


def test_invoke_skill_writes_agent_artifacts_to_live_dir(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    fixtures_dir = evals_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)
    (fixtures_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

    # Act
    live_dir = _invoke_skill("dataviz", evals_dir, FakeAgentPort())

    # Assert
    assert live_dir == fixtures_dir / "_live"
    assert (live_dir / "dataviz.js").read_text(
        encoding="utf-8"
    ) == "new Chart(); series"


def test_run_behave_skips_live_pass_when_live_dir_is_static(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    evals_dir = tmp_path / "evals"
    fixtures_dir = evals_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)
    calls: list[str] = []

    def fake_behave_pass(
        _evals_dir: Path, _artifacts_dir: Path, tag: str
    ) -> list[ScenarioResult]:
        calls.append(tag)
        return [ScenarioResult(feature="f", scenario=tag, status="passed")]

    monkeypatch.setattr("runner.run._behave_pass", fake_behave_pass)

    # Act
    results = _run_behave(evals_dir, fixtures_dir)

    # Assert
    assert calls == ["golden"]
    assert results[0].scenario == "golden"


def test_run_judge_uses_live_primary_chart_for_live_rubric(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    rubrics_dir = evals_dir / "rubrics"
    artifacts_dir = evals_dir / "fixtures" / "_live"
    rubrics_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)
    (rubrics_dir / "live.yaml").write_text(
        "rubrics:\n  - id: live\n    artifact_file: _live_primary_\n    prompt: pass\n",
        encoding="utf-8",
    )
    (artifacts_dir / "chart.js").write_text("new Chart();", encoding="utf-8")

    # Act
    verdicts = _run_judge(evals_dir, artifacts_dir, FakeJudgePort())

    # Assert
    assert verdicts == [
        JudgeReport(
            rubric_id="live",
            passed=True,
            score=_PASSING_SCORE,
            reasoning="judged new Chart();",
        )
    ]


def test_find_primary_chart_prefers_visualization_file(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "notes.txt").write_text("new Chart();", encoding="utf-8")
    (tmp_path / "chart.js").write_text("new Chart();", encoding="utf-8")

    # Act
    primary_chart = _find_primary_chart(tmp_path)

    # Assert
    assert primary_chart == tmp_path / "chart.js"


def test_extract_section_returns_requested_markdown_section() -> None:
    # Arrange
    content = "## Summary\nkeep\n## Details\nskip"

    # Act
    section = _extract_section(content, "Summary")

    # Assert
    assert section == "## Summary\nkeep"


def test_write_report_includes_failures_judge_scores_and_artifact_sizes(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    structural_results = [
        ScenarioResult(feature="f", scenario="valid chart", status="passed"),
        ScenarioResult(
            feature="f", scenario="bad chart", status="failed", failure="bad"
        ),
    ]
    judge_reports = [
        JudgeReport(
            rubric_id="palette", passed=False, score=_FAILING_SCORE, reasoning="weak"
        )
    ]

    # Act
    report_path = _write_report(
        "dataviz",
        evals_dir,
        "all",
        structural_results,
        judge_reports,
        {"chart.js": len("chart")},
    )

    # Assert
    report = report_path.read_text(encoding="utf-8")
    assert "bad chart" in report
    assert "palette" in report
    assert f"Pass rate**: 1/{_EXPECTED_REPORT_CHECKS}" in report


def test_evaluate_skill_returns_false_when_judge_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    evals_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "runner.run._run_judge",
        lambda _evals_dir, _artifacts_dir, _judge: [
            JudgeReport(
                rubric_id="quality", passed=False, score=_FAILING_SCORE, reasoning="bad"
            )
        ],
    )

    # Act
    is_success = _evaluate_skill(
        evals_dir, "judge", adapter=None, judge=FakeJudgePort()
    )

    # Assert
    assert is_success is False
