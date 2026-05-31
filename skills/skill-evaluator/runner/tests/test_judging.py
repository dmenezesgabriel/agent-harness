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


def test_run_uses_live_primary_chart_for_live_rubric(tmp_path: Path) -> None:
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
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    rubrics_dir = evals_dir / "rubrics"
    fixtures_dir = evals_dir / "fixtures"
    live_dir = fixtures_dir / "_live"
    rubrics_dir.mkdir(parents=True)
    live_dir.mkdir(parents=True)
    (rubrics_dir / "static.yaml").write_text(
        "rubrics:\n  - id: static\n    artifact_file: golden.md\n    prompt: pass\n",
        encoding="utf-8",
    )
    (fixtures_dir / "golden.md").write_text("golden content", encoding="utf-8")

    # Act
    verdicts = RubricJudgeRunner().run(evals_dir, live_dir, FakeRubricJudge())

    # Assert
    assert verdicts[0].reasoning == "judged golden content"


def test_run_skips_when_rubrics_dir_is_missing(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    artifacts_dir = evals_dir / "fixtures"
    artifacts_dir.mkdir(parents=True)

    # Act
    verdicts = RubricJudgeRunner().run(evals_dir, artifacts_dir, FakeRubricJudge())

    # Assert
    assert verdicts == []


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
