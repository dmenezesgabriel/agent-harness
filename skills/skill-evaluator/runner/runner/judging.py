from __future__ import annotations

import re
import time
from contextlib import suppress
from pathlib import Path

import structlog
import yaml

from runner.models import JudgeReport, RubricFile
from runner.ports import CompareJudgePort, JudgePort

_log = structlog.get_logger()


class RubricJudgeRunner:
    """Evaluate rubric files against golden or live artifacts.

    Usage:
        reports = RubricJudgeRunner().run(evals_dir, artifacts_dir, judge)
    """

    def run(
        self,
        evals_dir: Path,
        artifacts_dir: Path,
        judge: JudgePort,
        generated_only: bool = False,
    ) -> list[JudgeReport]:
        rubrics_dir = evals_dir / "rubrics"
        if not rubrics_dir.exists():
            print("  No rubrics/ directory found - skipping judge")
            return []

        primary_chart: Path | None = None
        verdicts: list[JudgeReport] = []
        for rubric_file in sorted(rubrics_dir.glob("*.yaml")):
            rubric_file_model = RubricFile.model_validate(
                yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
            )
            for rubric in rubric_file_model.rubrics:
                if (
                    generated_only
                    and rubric.artifact_file != "_generated_artifacts_primary_"
                ):
                    continue
                if (
                    rubric.artifact_file == "_generated_artifacts_primary_"
                    and primary_chart is None
                ):
                    primary_chart = _find_primary_chart(artifacts_dir)
                artifact_file = _resolve_artifact_file(
                    evals_dir, rubric.artifact_file, primary_chart
                )
                if artifact_file is None:
                    print(
                        f"  Rubric {rubric.id!r}: no primary chart artifact found - skipping"
                    )
                    continue
                if not artifact_file.exists():
                    print(
                        f"  Rubric {rubric.id!r}: fixture {rubric.artifact_file!r} not found - skipping"
                    )
                    continue

                content = artifact_file.read_text(encoding="utf-8")
                if rubric.artifact_section:
                    content = _extract_section(content, rubric.artifact_section)
                _log.info(
                    "judge_start", rubric_id=rubric.id, artifact_chars=len(content)
                )
                t0 = time.monotonic()
                verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
                _log.info(
                    "judge_done",
                    rubric_id=rubric.id,
                    elapsed_s=round(time.monotonic() - t0, 1),
                )
                verdicts.append(JudgeReport.model_validate(verdict.model_dump()))

        self._print_summary(verdicts)
        return verdicts

    def compare_run(
        self,
        evals_dir: Path,
        skill_dir: Path,
        baseline_dir: Path,
        judge: CompareJudgePort,
    ) -> tuple[list[JudgeReport], list[JudgeReport]]:
        """One judge call per generated rubric instead of two.

        Non-generated rubrics (golden fixtures) are judged on skill output only.
        Returns (skill_verdicts, baseline_verdicts).

        Usage:
            skill_v, baseline_v = runner.compare_run(evals_dir, skill_dir, baseline_dir, judge)
        """
        rubrics_dir = evals_dir / "rubrics"
        if not rubrics_dir.exists():
            print("  No rubrics/ directory found - skipping judge")
            return [], []

        skill_primary: Path | None = None
        baseline_primary: Path | None = None
        skill_verdicts: list[JudgeReport] = []
        baseline_verdicts: list[JudgeReport] = []

        for rubric_file in sorted(rubrics_dir.glob("*.yaml")):
            rubric_file_model = RubricFile.model_validate(
                yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
            )
            for rubric in rubric_file_model.rubrics:
                if rubric.artifact_file == "_generated_artifacts_primary_":
                    skill_primary = skill_primary or _find_primary_chart(skill_dir)
                    baseline_primary = baseline_primary or _find_primary_chart(
                        baseline_dir
                    )
                    if skill_primary is None or baseline_primary is None:
                        print(
                            f"  Rubric {rubric.id!r}: chart artifact missing - skipping"
                        )
                        continue
                    skill_content = skill_primary.read_text(encoding="utf-8")
                    baseline_content = baseline_primary.read_text(encoding="utf-8")
                    _log.info(
                        "compare_judge_start",
                        rubric_id=rubric.id,
                        skill_chars=len(skill_content),
                        baseline_chars=len(baseline_content),
                    )
                    t0 = time.monotonic()
                    sv, bv = judge.compare_judge(
                        skill_content,
                        baseline_content,
                        rubric.prompt,
                        rubric_id=rubric.id,
                    )
                    _log.info(
                        "compare_judge_done",
                        rubric_id=rubric.id,
                        elapsed_s=round(time.monotonic() - t0, 1),
                    )
                    skill_verdicts.append(JudgeReport.model_validate(sv.model_dump()))
                    baseline_verdicts.append(
                        JudgeReport.model_validate(bv.model_dump())
                    )
                else:
                    artifact_file = _resolve_artifact_file(
                        evals_dir, rubric.artifact_file, None
                    )
                    if artifact_file is None or not artifact_file.exists():
                        print(f"  Rubric {rubric.id!r}: fixture not found - skipping")
                        continue
                    content = artifact_file.read_text(encoding="utf-8")
                    if rubric.artifact_section:
                        content = _extract_section(content, rubric.artifact_section)
                    _log.info(
                        "judge_start", rubric_id=rubric.id, artifact_chars=len(content)
                    )
                    t0 = time.monotonic()
                    verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
                    _log.info(
                        "judge_done",
                        rubric_id=rubric.id,
                        elapsed_s=round(time.monotonic() - t0, 1),
                    )
                    skill_verdicts.append(
                        JudgeReport.model_validate(verdict.model_dump())
                    )

        self._print_compare_summary(skill_verdicts, baseline_verdicts)
        return skill_verdicts, baseline_verdicts

    def _print_compare_summary(
        self, skill_verdicts: list[JudgeReport], baseline_verdicts: list[JudgeReport]
    ) -> None:
        skill_passed = sum(1 for v in skill_verdicts if v.passed)
        baseline_passed = sum(1 for v in baseline_verdicts if v.passed)
        print(
            f"\n  Judge: {skill_passed} passed (skill), {baseline_passed} passed (baseline)"
        )
        baseline_by_id = {v.rubric_id: v for v in baseline_verdicts}
        for verdict in skill_verdicts:
            icon = "PASS" if verdict.passed else "FAIL"
            baseline = baseline_by_id.get(verdict.rubric_id)
            if baseline is not None:
                b_icon = "PASS" if baseline.passed else "FAIL"
                print(
                    f"    {icon}/{b_icon} {verdict.rubric_id} "
                    f"(skill={verdict.score:.2f}, baseline={baseline.score:.2f}): {verdict.reasoning}"
                )
            else:
                print(
                    f"    {icon} {verdict.rubric_id} (skill={verdict.score:.2f}): {verdict.reasoning}"
                )

    def _print_summary(self, verdicts: list[JudgeReport]) -> None:
        passed = sum(1 for verdict in verdicts if verdict.passed)
        failed = sum(1 for verdict in verdicts if not verdict.passed)
        print(f"\n  Judge: {passed} passed, {failed} failed")
        for verdict in verdicts:
            icon = "PASS" if verdict.passed else "FAIL"
            print(
                f"    {icon} {verdict.rubric_id} "
                f"(score={verdict.score:.2f}): {verdict.reasoning}"
            )


def _resolve_artifact_file(
    evals_dir: Path, artifact_name: str, primary_chart: Path | None
) -> Path | None:
    if artifact_name == "_generated_artifacts_primary_":
        return primary_chart
    return evals_dir / "fixtures" / "golden" / artifact_name


_VIZ_KEYWORDS_PAT = re.compile(
    r"new\s+Chart\b|Chart\.js"
    r"|plotly|go\.Figure|px\.\w+\("
    r"|alt\.Chart\b|\.mark_line\(\)|\.mark_bar\(\)"
    r"|import\s+matplotlib|plt\.(plot|bar|scatter)\b"
    r'|"mark"\s*:\s*"(?:line|bar|area|point)"'
    r"|<svg\b|createElementNS\([^)]*['\"]path['\"]"
    r"|d3\.select\b"
    r"|from\s+['\"](?:recharts|victory|echarts|highcharts|apexcharts|@nivo/\w+)['\"]"
    r"|(?:LineChart|BarChart|AreaChart|PieChart|ScatterChart)\b",
    re.IGNORECASE,
)
_VIZ_EXTENSIONS = (".html", ".js", ".jsx", ".tsx", ".py", ".ipynb", ".json")
_IGNORED_ARTIFACT_PARTS = frozenset({".git", "dist", "node_modules"})


def _find_primary_chart(artifacts_dir: Path) -> Path | None:
    """Return the largest visualization file in artifacts_dir.

    Size distinguishes entry-point scaffolds (small) from chart implementations
    (large) without requiring structural metadata about the project layout.
    """
    best: tuple[int, Path] | None = None
    for ext in _VIZ_EXTENSIONS:
        for path in sorted(artifacts_dir.rglob(f"*{ext}")):
            if _IGNORED_ARTIFACT_PARTS & set(path.relative_to(artifacts_dir).parts):
                continue
            with suppress(OSError):
                content = path.read_text(encoding="utf-8", errors="ignore")
                if not _VIZ_KEYWORDS_PAT.search(content):
                    continue
                size = len(content)
                if best is None or size > best[0]:
                    best = (size, path)
    return best[1] if best is not None else None


def _extract_section(content: str, heading: str) -> str:
    pattern = rf"##\s+{re.escape(heading)}.*?(?=\n##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else content
