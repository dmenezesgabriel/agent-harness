from pathlib import Path

from runner.judging import RubricJudgeRunner, _extract_section, _find_primary_chart
from runner.models import JudgeReport
from runner.ports import JudgeVerdict

_PASSING_SCORE = 0.9


class FakeRubricJudge:
    """Fake for regular judge() calls (non-compare mode)."""

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


class FakeCompareJudge:
    """Fake for compare_judge() calls — returns distinct scores for skill vs baseline."""

    def judge(
        self, _artifact_content: str, _rubric: str, rubric_id: str
    ) -> JudgeVerdict:
        return JudgeVerdict(
            rubric_id=rubric_id, passed=True, score=_PASSING_SCORE, reasoning="ok"
        )

    def compare_judge(
        self,
        skill_content: str,
        baseline_content: str,
        _rubric: str,
        rubric_id: str,
    ) -> tuple[JudgeVerdict, JudgeVerdict]:
        return (
            JudgeVerdict(
                rubric_id=rubric_id,
                passed=True,
                score=1.0,
                reasoning=f"skill: {skill_content[:10]}",
            ),
            JudgeVerdict(
                rubric_id=rubric_id,
                passed=False,
                score=0.3,
                reasoning=f"baseline: {baseline_content[:10]}",
            ),
        )


class TestCompareRun:
    def test_compare_run_calls_compare_judge_for_generated_rubric(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "evals"
        rubrics_dir = evals_dir / "rubrics"
        skill_dir = tmp_path / "skill"
        baseline_dir = tmp_path / "baseline"
        rubrics_dir.mkdir(parents=True)
        skill_dir.mkdir()
        baseline_dir.mkdir()
        (rubrics_dir / "gen.yaml").write_text(
            "rubrics:\n  - id: gen\n    artifact_file: _generated_artifacts_primary_\n    prompt: check\n",
            encoding="utf-8",
        )
        (skill_dir / "chart.js").write_text("new Chart(); skill", encoding="utf-8")
        (baseline_dir / "chart.js").write_text("new Chart(); base", encoding="utf-8")

        # Act
        skill_v, baseline_v = RubricJudgeRunner().compare_run(
            evals_dir, skill_dir, baseline_dir, FakeCompareJudge()
        )

        # Assert — one verdict each, derived from compare_judge
        assert [v.rubric_id for v in skill_v] == ["gen"]
        assert [v.rubric_id for v in baseline_v] == ["gen"]
        assert skill_v[0].score == 1.0
        assert baseline_v[0].score == 0.3

    def test_compare_run_non_generated_rubric_judges_skill_only(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "evals"
        rubrics_dir = evals_dir / "rubrics"
        golden_dir = evals_dir / "fixtures" / "golden"
        rubrics_dir.mkdir(parents=True)
        golden_dir.mkdir(parents=True)
        (golden_dir / "bar.js").write_text("new Chart();", encoding="utf-8")
        (rubrics_dir / "static.yaml").write_text(
            "rubrics:\n  - id: static\n    artifact_file: bar.js\n    prompt: pass\n",
            encoding="utf-8",
        )

        # Act
        skill_v, baseline_v = RubricJudgeRunner().compare_run(
            evals_dir, tmp_path / "skill", tmp_path / "baseline", FakeCompareJudge()
        )

        # Assert — skill gets a verdict, baseline gets none (no fixtures)
        assert [v.rubric_id for v in skill_v] == ["static"]
        assert baseline_v == []

    def test_compare_run_returns_empty_when_no_rubrics_dir(
        self, tmp_path: Path
    ) -> None:
        skill_v, baseline_v = RubricJudgeRunner().compare_run(
            tmp_path, tmp_path / "skill", tmp_path / "baseline", FakeCompareJudge()
        )
        assert skill_v == []
        assert baseline_v == []


class TestExtractSection:
    def test_extract_section_returns_requested_markdown_section(self) -> None:
        # Arrange
        content = "## Summary\nkeep\n## Details\nskip"

        # Act
        section = _extract_section(content, "Summary")

        # Assert
        assert section == "## Summary\nkeep"
