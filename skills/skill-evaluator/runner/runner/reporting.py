from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from pathlib import Path

from runner.models import JudgeReport, Mode, ScenarioResult, TriggerReport

_PERCENT_SCALE = 100


class SkillInputSizer:
    """Measure skill inputs with character counts as a token proxy.

    Usage:
        sizes = SkillInputSizer().measure(Path('skills/dataviz/evals'))
    """

    def measure(self, evals_dir: Path) -> dict[str, int]:
        sizes: dict[str, int] = {}
        skill_file = evals_dir.parent / "SKILL.md"
        _measure_file(skill_file, "SKILL.md", sizes)
        for input_file in sorted((evals_dir / "fixtures" / "inputs").glob("*.md")):
            _measure_file(input_file, f"fixtures/inputs/{input_file.name}", sizes)
        return sizes


class MarkdownReportWriter:
    """Write skill evaluation reports as markdown files.

    Usage:
        path = MarkdownReportWriter().write('dataviz', evals_dir, 'all', [], [])
    """

    def write(
        self,
        skill_name: str,
        evals_dir: Path,
        mode: Mode,
        structural_results: list[ScenarioResult],
        judge_verdicts: list[JudgeReport],
        input_sizes: dict[str, int] | None = None,
        trigger_report: TriggerReport | None = None,
    ) -> Path:
        reports_dir = evals_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        run_at = datetime.now()
        report_path = (
            reports_dir / f"{skill_name}-{run_at.strftime('%Y-%m-%dT%H-%M-%S-%f')}.md"
        )
        lines = _report_lines(
            mode, skill_name, run_at, structural_results, judge_verdicts, input_sizes, trigger_report
        )
        report_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )
        return report_path


def _report_lines(
    mode: Mode,
    skill_name: str,
    run_at: datetime,
    structural_results: list[ScenarioResult],
    judge_verdicts: list[JudgeReport],
    input_sizes: dict[str, int] | None,
    trigger_report: TriggerReport | None = None,
) -> list[str]:
    lines = [
        f"# Eval Report: {skill_name}",
        f"Run: {run_at.isoformat()} | Mode: {mode}",
        "",
    ]
    active_structural = [r for r in structural_results if r.status != "skipped"]
    lines += _structural_lines(active_structural)
    lines += _judge_lines(judge_verdicts)
    lines += _trigger_lines(trigger_report)
    lines += _input_size_lines(input_sizes)
    lines += _pass_rate_lines(active_structural, judge_verdicts, trigger_report)
    return lines


def _measure_file(path: Path, label: str, sizes: dict[str, int]) -> None:
    if not path.is_file():
        return
    with suppress(OSError, UnicodeDecodeError):
        sizes[label] = len(path.read_text(encoding="utf-8"))


def _structural_lines(active_structural: list[ScenarioResult]) -> list[str]:
    if not active_structural:
        return []
    lines = [
        "## Structural checks (behave)",
        "",
        "| Scenario | Result |",
        "|----------|--------|",
    ]
    for scenario in active_structural:
        icon = "PASS" if scenario.status == "passed" else "FAIL"
        lines.append(f"| {scenario.scenario} | {icon} |")
    failures = [
        scenario for scenario in active_structural if scenario.status == "failed"
    ]
    if failures:
        lines += ["", "### Failures", ""]
        for scenario in failures:
            lines.append(f"**{scenario.scenario}**: {scenario.failure}")
    lines.append("")
    return lines


def _judge_lines(judge_verdicts: list[JudgeReport]) -> list[str]:
    if not judge_verdicts:
        return []
    lines = ["## LLM-as-judge checks", "", "| Rubric | Score | Result | Reasoning |"]
    lines.append("|--------|-------|--------|-----------|")
    for verdict in judge_verdicts:
        icon = "PASS" if verdict.passed else "FAIL"
        lines.append(
            f"| {verdict.rubric_id} | {verdict.score:.2f} | {icon} | {verdict.reasoning} |"
        )
    lines.append("")
    return lines


def _trigger_lines(trigger_report: TriggerReport | None) -> list[str]:
    if not trigger_report or not trigger_report.results:
        return []
    lines = [
        "## Trigger routing checks",
        "",
        "| Query | Expected | Actual | Result |",
        "|-------|----------|--------|--------|",
    ]
    for r in trigger_report.results:
        expected = "INVOKE" if r.expected else "SKIP"
        actual = "INVOKE" if r.actual else "SKIP"
        icon = "PASS" if r.passed else "FAIL"
        lines.append(f"| {r.query} | {expected} | {actual} | {icon} |")
    pct = int(_PERCENT_SCALE * trigger_report.pass_rate)
    passed_count = sum(1 for r in trigger_report.results if r.passed)
    total = len(trigger_report.results)
    overall = "PASS" if trigger_report.passed else "FAIL"
    lines += ["", f"**Trigger accuracy**: {passed_count}/{total} ({pct}%) — {overall}", ""]
    return lines


def _input_size_lines(input_sizes: dict[str, int] | None) -> list[str]:
    if not input_sizes:
        return []
    total_chars = sum(input_sizes.values())
    lines = ["## Skill input size (chars - proxy for tokens)", ""]
    lines += ["| File | Characters |", "|------|-----------|"]
    for rel_path, size in sorted(input_sizes.items()):
        lines.append(f"| {rel_path} | {size:,} |")
    lines.append(f"| **Total** | **{total_chars:,}** |")
    lines.append("")
    return lines


def _pass_rate_lines(
    active_structural: list[ScenarioResult],
    judge_verdicts: list[JudgeReport],
    trigger_report: TriggerReport | None = None,
) -> list[str]:
    structural_passes = sum(
        1 for scenario in active_structural if scenario.status == "passed"
    )
    judge_passes = sum(1 for verdict in judge_verdicts if verdict.passed)
    trigger_passes = sum(1 for r in trigger_report.results if r.passed) if trigger_report else 0
    trigger_total = len(trigger_report.results) if trigger_report else 0
    total_checks = len(active_structural) + len(judge_verdicts) + trigger_total
    if not total_checks:
        return []
    total_passes = structural_passes + judge_passes + trigger_passes
    pct = int(_PERCENT_SCALE * total_passes / total_checks)
    return [f"**Pass rate**: {total_passes}/{total_checks} ({pct}%)"]
