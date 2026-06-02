import re
from pathlib import Path

from runner.models import JudgeReport, Mode, ScenarioResult
from runner.reporting import MarkdownReportWriter, SkillInputSizer

_FAILING_SCORE = 0.2
_EXPECTED_REPORT_CHECKS = 3


class TestSkillInputSizer:
    def test_skill_input_sizer_counts_skill_and_input_fixture_chars(
        self,
        tmp_path: Path,
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        inputs_dir = evals_dir / "fixtures" / "inputs"
        inputs_dir.mkdir(parents=True)
        (tmp_path / "dataviz" / "SKILL.md").write_text("skill rules", encoding="utf-8")
        (inputs_dir / "input_timeseries.md").write_text(
            "chart prompt", encoding="utf-8"
        )

        # Act
        sizes = SkillInputSizer().measure(evals_dir)

        # Assert
        assert sizes == {
            "SKILL.md": len("skill rules"),
            "fixtures/inputs/input_timeseries.md": len("chart prompt"),
        }


class TestMarkdownReportWriter:
    def test_write_uses_unique_timestamped_name_and_includes_input_sizes(
        self,
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
                rubric_id="palette",
                passed=False,
                score=_FAILING_SCORE,
                reasoning="weak",
            )
        ]

        # Act
        report_path = MarkdownReportWriter().write(
            "dataviz",
            evals_dir,
            Mode.ALL,
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


class TestMarkdownReportWriterComparison:
    def test_empty_when_no_baseline(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        report = (
            MarkdownReportWriter()
            .write("dataviz", evals_dir, Mode.ALL, [], [], None)
            .read_text(encoding="utf-8")
        )
        assert "Baseline comparison" not in report

    def test_shows_skill_vs_baseline_per_check(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        skill_results = [
            ScenarioResult(feature="f", scenario="has_chart", status="passed"),
            ScenarioResult(feature="f", scenario="has_title", status="failed"),
        ]
        baseline_results = [
            ScenarioResult(feature="f", scenario="has_chart", status="failed"),
            ScenarioResult(feature="f", scenario="has_title", status="failed"),
        ]

        # Act
        report = (
            MarkdownReportWriter()
            .write(
                "dataviz",
                evals_dir,
                Mode.COMPARE,
                skill_results,
                [],
                None,
                None,
                baseline_results,
            )
            .read_text(encoding="utf-8")
        )

        # Assert — skill passed where baseline failed on has_chart
        assert "has_chart" in report
        assert "| PASS | FAIL |" in report

    def test_delta_label_shows_skill_gain_over_baseline(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        skill_results = [
            ScenarioResult(feature="f", scenario="c1", status="passed"),
            ScenarioResult(feature="f", scenario="c2", status="passed"),
        ]
        baseline_results = [
            ScenarioResult(feature="f", scenario="c1", status="failed"),
            ScenarioResult(feature="f", scenario="c2", status="passed"),
        ]

        # Act
        report = (
            MarkdownReportWriter()
            .write(
                "dataviz",
                evals_dir,
                Mode.COMPARE,
                skill_results,
                [],
                None,
                None,
                baseline_results,
            )
            .read_text(encoding="utf-8")
        )

        # Assert — skill gained 1 check (+1) over baseline
        assert "+1" in report

    def test_includes_comparison_section_when_baseline_provided(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        skill_results = [
            ScenarioResult(feature="f", scenario="has_chart", status="passed")
        ]
        baseline_results = [
            ScenarioResult(feature="f", scenario="has_chart", status="failed")
        ]

        # Act
        report_path = MarkdownReportWriter().write(
            "dataviz",
            evals_dir,
            Mode.COMPARE,
            skill_results,
            [],
            None,
            None,
            baseline_structural_results=baseline_results,
        )

        # Assert
        report = report_path.read_text(encoding="utf-8")
        assert "Baseline comparison" in report
        assert "+1" in report

    def test_omits_comparison_section_when_no_baseline(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"

        # Act
        report_path = MarkdownReportWriter().write(
            "dataviz", evals_dir, Mode.INVOKE, [], [], None
        )

        # Assert
        assert "Baseline comparison" not in report_path.read_text(encoding="utf-8")


class TestMarkdownReportWriterJudgeComparison:
    def test_renders_judge_comparison_section_with_delta(self, tmp_path: Path) -> None:
        """UT-003 / AC-002 / AC-005: judge comparison table with correct delta values."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        skill_verdicts = [
            JudgeReport(rubric_id="palette", passed=True, score=0.9, reasoning="good")
        ]
        baseline_verdicts = [
            JudgeReport(rubric_id="palette", passed=False, score=0.6, reasoning="weak")
        ]

        # Act
        report = (
            MarkdownReportWriter()
            .write(
                "dataviz",
                evals_dir,
                Mode.COMPARE,
                [],
                skill_verdicts,
                baseline_judge_verdicts=baseline_verdicts,
            )
            .read_text(encoding="utf-8")
        )

        # Assert
        assert "## Judge comparison" in report
        assert "palette" in report
        assert "0.90" in report
        assert "0.60" in report
        assert "+0.30" in report

    def test_omits_judge_comparison_section_when_no_baseline_verdicts(
        self, tmp_path: Path
    ) -> None:
        """UT-004 / AC-003 / FR-007: section is absent when baseline_judge_verdicts is empty."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        skill_verdicts = [
            JudgeReport(rubric_id="palette", passed=True, score=0.9, reasoning="good")
        ]

        # Act
        report = (
            MarkdownReportWriter()
            .write(
                "dataviz",
                evals_dir,
                Mode.COMPARE,
                [],
                skill_verdicts,
                baseline_judge_verdicts=[],
            )
            .read_text(encoding="utf-8")
        )

        # Assert
        assert "## Judge comparison" not in report

    def test_omits_judge_comparison_section_when_baseline_verdicts_is_none(
        self, tmp_path: Path
    ) -> None:
        """FR-007: section is absent when baseline_judge_verdicts is None."""
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"

        # Act
        report = (
            MarkdownReportWriter()
            .write("dataviz", evals_dir, Mode.COMPARE, [], [])
            .read_text(encoding="utf-8")
        )

        # Assert
        assert "## Judge comparison" not in report
