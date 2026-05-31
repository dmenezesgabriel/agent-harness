from __future__ import annotations

import re
import time
from contextlib import suppress
from pathlib import Path

import structlog
import yaml

_log = structlog.get_logger()

from runner.models import JudgeReport, RubricFile
from runner.ports import JudgePort


class RubricJudgeRunner:
    """Evaluate rubric files against golden or live artifacts.

    Usage:
        reports = RubricJudgeRunner().run(evals_dir, artifacts_dir, judge)
    """

    def run(
        self, evals_dir: Path, artifacts_dir: Path, judge: JudgePort
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
                if rubric.artifact_file == "_generated_artifacts_primary_" and primary_chart is None:
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
                _log.info("judge_start", rubric_id=rubric.id, artifact_chars=len(content))
                t0 = time.monotonic()
                verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
                _log.info("judge_done", rubric_id=rubric.id, elapsed_s=round(time.monotonic() - t0, 1))
                verdicts.append(JudgeReport.model_validate(verdict.model_dump()))

        self._print_summary(verdicts)
        return verdicts

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
    """Return the first visualization file found in artifacts_dir, by extension priority."""
    for ext in _VIZ_EXTENSIONS:
        candidates = sorted(artifacts_dir.rglob(f"*{ext}"))
        for path in candidates:
            if _IGNORED_ARTIFACT_PARTS & set(path.relative_to(artifacts_dir).parts):
                continue
            with suppress(OSError):
                if _VIZ_KEYWORDS_PAT.search(
                    path.read_text(encoding="utf-8", errors="ignore")
                ):
                    return path
    return None


def _extract_section(content: str, heading: str) -> str:
    pattern = rf"##\s+{re.escape(heading)}.*?(?=\n##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else content
