import re
from pathlib import Path

from runner.models import JudgeReport, ScenarioResult
from runner.reporting import MarkdownReportWriter, SkillInputSizer

_FAILING_SCORE = 0.2
_EXPECTED_REPORT_CHECKS = 3


def test_skill_input_sizer_counts_skill_and_input_fixture_chars(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    inputs_dir = evals_dir / "fixtures" / "inputs"
    inputs_dir.mkdir(parents=True)
    (tmp_path / "dataviz" / "SKILL.md").write_text("skill rules", encoding="utf-8")
    (inputs_dir / "input_timeseries.md").write_text("chart prompt", encoding="utf-8")

    # Act
    sizes = SkillInputSizer().measure(evals_dir)

    # Assert
    assert sizes == {
        "SKILL.md": len("skill rules"),
        "fixtures/inputs/input_timeseries.md": len("chart prompt"),
    }


def test_write_uses_unique_timestamped_name_and_includes_input_sizes(
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
    report_path = MarkdownReportWriter().write(
        "dataviz",
        evals_dir,
        "all",
        structural_results,
        judge_reports,
        {"SKILL.md": len("skill rules")},
    )

    # Assert
    report = report_path.read_text(encoding="utf-8")
    assert re.match(
        r"dataviz-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6}\.md", report_path.name
    )
    assert "bad chart" in report
    assert "palette" in report
    assert "Skill input size" in report
    assert "SKILL.md" in report
    assert f"Pass rate**: 1/{_EXPECTED_REPORT_CHECKS}" in report
