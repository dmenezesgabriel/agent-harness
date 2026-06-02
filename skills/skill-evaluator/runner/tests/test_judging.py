from pathlib import Path

from runner.judging import RubricJudgeRunner, _extract_section, _find_primary_chart
from runner.models import JudgeReport
from runner.ports import JudgeVerdict

_PASSING_SCORE = 0.9


class FakeRubricJudge:
    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeVerdict:
        return JudgeVerdict(
            rubric_id=rubric_id,
            passed="pass" in rubric,
            score=_PASSING_SCORE,
            reasoning=f"judged {artifact_content}",
        )


class TestRubricJudgeRunner:
    def test_run_resolves_generated_artifacts_primary_sentinel(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        rubrics_dir = evals_dir / "rubrics"
        artifacts_dir = evals_dir / "fixtures" / "_generated_artifacts"
        rubrics_dir.mkdir(parents=True)
        artifacts_dir.mkdir(parents=True)
        (rubrics_dir / "live.yaml").write_text(
            "rubrics:\n  - id: live\n    artifact_file: _generated_artifacts_primary_\n    prompt: pass\n",
            encoding="utf-8",
        )
        (artifacts_dir / "chart.js").write_text("new Chart();", encoding="utf-8")

        # Act
        verdicts = RubricJudgeRunner().run(evals_dir, artifacts_dir, FakeRubricJudge())

        # Assert
        assert verdicts == [
            JudgeReport(
                rubric_id="live",
                passed=True,
                score=_PASSING_SCORE,
                reasoning="judged new Chart();",
            )
        ]

    def test_run_resolves_static_fixture_from_golden_dir_in_all_mode(
        self,
        tmp_path: Path,
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        rubrics_dir = evals_dir / "rubrics"
        fixtures_dir = evals_dir / "fixtures"
        generated_artifacts_dir = fixtures_dir / "_generated_artifacts"
        golden_dir = fixtures_dir / "golden"
        rubrics_dir.mkdir(parents=True)
        generated_artifacts_dir.mkdir(parents=True)
        golden_dir.mkdir(parents=True)
        (rubrics_dir / "static.yaml").write_text(
            "rubrics:\n  - id: static\n    artifact_file: golden.md\n    prompt: pass\n",
            encoding="utf-8",
        )
        (golden_dir / "golden.md").write_text("golden content", encoding="utf-8")

        # Act
        verdicts = RubricJudgeRunner().run(
            evals_dir, generated_artifacts_dir, FakeRubricJudge()
        )

        # Assert
        assert verdicts[0].reasoning == "judged golden content"

    def test_generated_only_skips_fixture_rubrics(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        rubrics_dir = evals_dir / "rubrics"
        artifacts_dir = evals_dir / "fixtures" / "_generated_artifacts"
        golden_dir = evals_dir / "fixtures" / "golden"
        rubrics_dir.mkdir(parents=True)
        artifacts_dir.mkdir(parents=True)
        golden_dir.mkdir(parents=True)
        (golden_dir / "bar.js").write_text("new Chart();", encoding="utf-8")
        (artifacts_dir / "chart.js").write_text("new Chart();", encoding="utf-8")
        (rubrics_dir / "mixed.yaml").write_text(
            "rubrics:\n"
            "  - id: fixture_rubric\n"
            "    artifact_file: bar.js\n"
            "    prompt: pass\n"
            "  - id: generated_rubric\n"
            "    artifact_file: _generated_artifacts_primary_\n"
            "    prompt: pass\n",
            encoding="utf-8",
        )

        # Act
        verdicts = RubricJudgeRunner().run(
            evals_dir, artifacts_dir, FakeRubricJudge(), generated_only=True
        )

        # Assert — only the generated rubric ran
        assert [v.rubric_id for v in verdicts] == ["generated_rubric"]

    def test_run_skips_when_rubrics_dir_is_missing(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        artifacts_dir = evals_dir / "fixtures"
        artifacts_dir.mkdir(parents=True)

        # Act
        verdicts = RubricJudgeRunner().run(evals_dir, artifacts_dir, FakeRubricJudge())

        # Assert
        assert verdicts == []


class TestFindPrimaryChart:
    def test_find_primary_chart_prefers_visualization_file(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "notes.txt").write_text("new Chart();", encoding="utf-8")
        (tmp_path / "chart.js").write_text("new Chart();", encoding="utf-8")

        # Act
        primary_chart = _find_primary_chart(tmp_path)

        # Assert
        assert primary_chart == tmp_path / "chart.js"


class TestExtractSection:
    def test_extract_section_returns_requested_markdown_section(self) -> None:
        # Arrange
        content = "## Summary\nkeep\n## Details\nskip"

        # Act
        section = _extract_section(content, "Summary")

        # Assert
        assert section == "## Summary\nkeep"
