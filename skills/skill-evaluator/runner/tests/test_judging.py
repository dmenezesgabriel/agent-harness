from pathlib import Path

from runner.judging import RubricJudgeRunner, _extract_section, _select_artifact
from runner.models import ArtifactSelector, JudgeReport

_PASSING_SCORE = 0.9


class FakeRubricJudge:
    """Fake for regular judge() calls (non-compare mode)."""

    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeReport:
        return JudgeReport(
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
            "rubrics:\n"
            "  - id: live\n"
            "    artifact_file: _generated_artifacts_primary_\n"
            "    artifact_selector:\n"
            "      extensions: ['.js']\n"
            "      content_patterns: ['new Chart']\n"
            "    prompt: pass\n",
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

    def test_run_skips_when_rubrics_dir_is_missing(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        artifacts_dir = evals_dir / "fixtures"
        artifacts_dir.mkdir(parents=True)

        # Act
        verdicts = RubricJudgeRunner().run(evals_dir, artifacts_dir, FakeRubricJudge())

        # Assert
        assert verdicts == []

    def test_run_fails_generated_rubric_without_artifact_selector(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        rubrics_dir = evals_dir / "rubrics"
        artifacts_dir = evals_dir / "fixtures" / "_generated_artifacts"
        rubrics_dir.mkdir(parents=True)
        artifacts_dir.mkdir(parents=True)
        (rubrics_dir / "live.yaml").write_text(
            "rubrics:\n"
            "  - id: live\n"
            "    artifact_file: _generated_artifacts_primary_\n"
            "    prompt: pass\n",
            encoding="utf-8",
        )
        (artifacts_dir / "chart.js").write_text("new Chart();", encoding="utf-8")

        # Act
        verdicts = RubricJudgeRunner().run(evals_dir, artifacts_dir, FakeRubricJudge())

        # Assert
        assert verdicts == [
            JudgeReport(
                rubric_id="live",
                passed=False,
                score=0.0,
                reasoning="No generated artifact matched the rubric artifact_selector.",
            )
        ]


class TestSelectArtifact:
    def test_select_artifact_matches_explicit_extension_and_content(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "notes.txt").write_text("new Chart();", encoding="utf-8")
        (tmp_path / "chart.js").write_text("new Chart();", encoding="utf-8")

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(extensions=[".js"], content_patterns=[r"new\s+Chart"]),
        )

        # Assert
        assert artifact == tmp_path / "chart.js"

    def test_select_artifact_selects_largest_matching_file(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "index.html").write_text(
            '<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js">'
            '</script><script type="module" src="/src/main.js"></script>',
            encoding="utf-8",
        )
        (tmp_path / "src").mkdir()
        large_javascript = (
            "new Chart(ctx, {type: 'line', data: {datasets: []}, options: {}});\n" * 50
        )
        (tmp_path / "src" / "main.js").write_text(large_javascript, encoding="utf-8")

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(extensions=[".html", ".js"], content_patterns=[r"Chart"]),
        )

        # Assert
        assert artifact == tmp_path / "src" / "main.js"

    def test_select_artifact_uses_path_and_content_filters(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "notes.md").write_text("# Task\nwrong path", encoding="utf-8")
        (tmp_path / "tasks" / "issues").mkdir(parents=True)
        (tmp_path / "tasks" / "issues" / "001-small.md").write_text(
            "# Task\nshort", encoding="utf-8"
        )
        (tmp_path / "tasks" / "issues" / "002-large.md").write_text(
            "# Task\n## Acceptance Criteria\n" + "detailed plan\n" * 20,
            encoding="utf-8",
        )

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(
                extensions=[".md"],
                path_patterns=["tasks/issues/*.md"],
                content_patterns=[r"## Acceptance Criteria"],
            ),
        )

        # Assert
        assert artifact == tmp_path / "tasks" / "issues" / "002-large.md"

    def test_select_artifact_can_return_first_match_instead_of_largest(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "tasks" / "issues").mkdir(parents=True)
        (tmp_path / "tasks" / "issues" / "001-small.md").write_text(
            "# Task\nshort", encoding="utf-8"
        )
        (tmp_path / "tasks" / "issues" / "002-large.md").write_text(
            "# Task\n" + "detailed plan\n" * 20, encoding="utf-8"
        )

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(
                extensions=[".md"],
                path_patterns=["tasks/issues/*.md"],
                prefer_largest=False,
            ),
        )

        # Assert
        assert artifact == tmp_path / "tasks" / "issues" / "001-small.md"

    def test_select_artifact_returns_none_without_explicit_match(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "tasks" / "issues").mkdir(parents=True)
        (tmp_path / "tasks" / "issues" / "001-task.md").write_text(
            "# Task\nmissing acceptance heading", encoding="utf-8"
        )

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(
                extensions=[".md"],
                path_patterns=["tasks/issues/*.md"],
                content_patterns=[r"## Acceptance Criteria"],
            ),
        )

        # Assert
        assert artifact is None

    def test_select_artifact_excludes_matching_path_patterns(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        (tmp_path / "package-lock.json").write_text(
            '{"dependencies":{"chart.js":"4.0.0"}}' * 20, encoding="utf-8"
        )
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.js").write_text("new Chart();", encoding="utf-8")

        # Act
        artifact = _select_artifact(
            tmp_path,
            ArtifactSelector(
                extensions=[".js", ".json"],
                exclude_path_patterns=["package*.json"],
                content_patterns=[r"Chart"],
            ),
        )

        # Assert
        assert artifact == tmp_path / "src" / "main.js"


class FakeCompareJudge:
    """Fake for compare_judge() calls — returns distinct scores for skill vs baseline."""

    def judge(
        self, _artifact_content: str, _rubric: str, rubric_id: str
    ) -> JudgeReport:
        return JudgeReport(
            rubric_id=rubric_id, passed=True, score=_PASSING_SCORE, reasoning="ok"
        )

    def compare_judge(
        self,
        skill_content: str,
        baseline_content: str,
        _rubric: str,
        rubric_id: str,
    ) -> tuple[JudgeReport, JudgeReport]:
        return (
            JudgeReport(
                rubric_id=rubric_id,
                passed=True,
                score=1.0,
                reasoning=f"skill: {skill_content[:10]}",
            ),
            JudgeReport(
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
            "rubrics:\n"
            "  - id: gen\n"
            "    artifact_file: _generated_artifacts_primary_\n"
            "    artifact_selector:\n"
            "      extensions: ['.js']\n"
            "      content_patterns: ['new Chart']\n"
            "    prompt: check\n",
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
