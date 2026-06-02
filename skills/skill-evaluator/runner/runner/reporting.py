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
        path = MarkdownReportWriter().write('dataviz', evals_dir, Mode.ALL, [], [])
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
        baseline_structural_results: list[ScenarioResult] | None = None,
        baseline_judge_verdicts: list[JudgeReport] | None = None,
    ) -> Path:
        reports_dir = evals_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        run_at = datetime.now()
        report_path = (
            reports_dir / f"{skill_name}-{run_at.strftime('%Y-%m-%dT%H-%M-%S-%f')}.md"
        )
        lines = self._report_lines(
            mode=mode,
            skill_name=skill_name,
            run_at=run_at,
            structural_results=structural_results,
            judge_verdicts=judge_verdicts,
            input_sizes=input_sizes,
            trigger_report=trigger_report,
            baseline_structural_results=baseline_structural_results,
            baseline_judge_verdicts=baseline_judge_verdicts,
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

    @staticmethod
    def _status_icon(passed: bool) -> str:
        return "PASS" if passed else "FAIL"

    @staticmethod
    def _report_lines(
        mode: Mode,
        skill_name: str,
        run_at: datetime,
        structural_results: list[ScenarioResult],
        judge_verdicts: list[JudgeReport],
        input_sizes: dict[str, int] | None,
        trigger_report: TriggerReport | None = None,
        baseline_structural_results: list[ScenarioResult] | None = None,
        baseline_judge_verdicts: list[JudgeReport] | None = None,
    ) -> list[str]:
        lines = [
            f"# Eval Report: {skill_name}",
            f"Run: {run_at.isoformat()} | Mode: {mode}",
            "",
        ]
        active_structural = [r for r in structural_results if r.status != "skipped"]
        lines += MarkdownReportWriter._structural_lines(active_structural)
        lines += MarkdownReportWriter._comparison_lines(
            active_structural, baseline_structural_results
        )
        lines += MarkdownReportWriter._judge_lines(judge_verdicts)
        lines += MarkdownReportWriter._judge_comparison_lines(
            judge_verdicts, baseline_judge_verdicts
        )
        lines += MarkdownReportWriter._trigger_lines(trigger_report)
        lines += MarkdownReportWriter._input_size_lines(input_sizes)
        lines += MarkdownReportWriter._pass_rate_lines(
            active_structural, judge_verdicts, trigger_report
        )
        return lines

    @staticmethod
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
            icon = MarkdownReportWriter._status_icon(scenario.status == "passed")
            lines.append(f"| {scenario.scenario} | {icon} |")
        failures = [s for s in active_structural if s.status == "failed"]
        if failures:
            lines += ["", "### Failures", ""]
            for scenario in failures:
                lines.append(f"**{scenario.scenario}**: {scenario.failure}")
        lines.append("")
        return lines

    @staticmethod
    def _comparison_lines(
        structural_results: list[ScenarioResult],
        baseline_results: list[ScenarioResult] | None,
    ) -> list[str]:
        if not baseline_results:
            return []
        baseline_by_scenario = {r.scenario: r for r in baseline_results}
        generated = [r for r in structural_results if "generated" in r.feature.lower()]
        if not generated:
            return []
        skill_passes = sum(1 for r in generated if r.status == "passed")
        baseline_passes = sum(
            1
            for r in generated
            if (b := baseline_by_scenario.get(r.scenario)) is not None
            and b.status == "passed"
        )
        delta = skill_passes - baseline_passes
        delta_label = f"+{delta}" if delta >= 0 else str(delta)
        return [
            "## Baseline comparison",
            "",
            "| Check | Skill | Baseline |",
            "|-------|-------|----------|",
            *MarkdownReportWriter._comparison_rows(generated, baseline_by_scenario),
            "",
            f"**Skill improvement**: {delta_label} checks vs baseline ({skill_passes} skill / {baseline_passes} baseline)",
            "",
        ]

    @staticmethod
    def _comparison_rows(
        structural_results: list[ScenarioResult],
        baseline_by_scenario: dict[str, ScenarioResult],
    ) -> list[str]:
        rows = []
        for result in structural_results:
            skill_icon = MarkdownReportWriter._status_icon(result.status == "passed")
            baseline = baseline_by_scenario.get(result.scenario)
            baseline_icon = MarkdownReportWriter._status_icon(
                baseline is not None and baseline.status == "passed"
            )
            rows.append(f"| {result.scenario} | {skill_icon} | {baseline_icon} |")
        return rows

    @staticmethod
    def _judge_lines(judge_verdicts: list[JudgeReport]) -> list[str]:
        if not judge_verdicts:
            return []
        lines = [
            "## LLM-as-judge checks",
            "",
            "| Rubric | Score | Result | Reasoning |",
        ]
        lines.append("|--------|-------|--------|-----------|")
        for verdict in judge_verdicts:
            icon = MarkdownReportWriter._status_icon(verdict.passed)
            lines.append(
                f"| {verdict.rubric_id} | {verdict.score:.2f} | {icon} | {verdict.reasoning} |"
            )
        lines.append("")
        return lines

    @staticmethod
    def _judge_comparison_lines(
        judge_verdicts: list[JudgeReport],
        baseline_judge_verdicts: list[JudgeReport] | None,
    ) -> list[str]:
        if not baseline_judge_verdicts:
            return []
        baseline_by_id = {v.rubric_id: v for v in baseline_judge_verdicts}
        lines = [
            "## Judge comparison",
            "",
            "| Rubric | Skill | Baseline | Delta |",
            "|--------|-------|----------|-------|",
        ]
        for verdict in judge_verdicts:
            baseline = baseline_by_id.get(verdict.rubric_id)
            if baseline is None:
                continue
            delta = verdict.score - baseline.score
            delta_label = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
            lines.append(
                f"| {verdict.rubric_id} | {verdict.score:.2f} | {baseline.score:.2f} | {delta_label} |"
            )
        lines.append("")
        return lines

    @staticmethod
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
            icon = MarkdownReportWriter._status_icon(r.passed)
            lines.append(f"| {r.query} | {expected} | {actual} | {icon} |")
        pass_percent = int(_PERCENT_SCALE * trigger_report.pass_rate)
        passed_count = sum(1 for r in trigger_report.results if r.passed)
        total = len(trigger_report.results)
        overall = MarkdownReportWriter._status_icon(trigger_report.passed)
        lines += [
            "",
            f"**Trigger accuracy**: {passed_count}/{total} ({pass_percent}%) — {overall}",
            "",
        ]
        return lines

    @staticmethod
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

    @staticmethod
    def _pass_rate_lines(
        active_structural: list[ScenarioResult],
        judge_verdicts: list[JudgeReport],
        trigger_report: TriggerReport | None = None,
    ) -> list[str]:
        structural_passes = sum(1 for s in active_structural if s.status == "passed")
        judge_passes = sum(1 for v in judge_verdicts if v.passed)
        trigger_passes = (
            sum(1 for r in trigger_report.results if r.passed) if trigger_report else 0
        )
        trigger_total = len(trigger_report.results) if trigger_report else 0
        total_checks = len(active_structural) + len(judge_verdicts) + trigger_total
        if not total_checks:
            return []
        total_passes = structural_passes + judge_passes + trigger_passes
        pass_percent = int(_PERCENT_SCALE * total_passes / total_checks)
        return [f"**Pass rate**: {total_passes}/{total_checks} ({pass_percent}%)"]


def _measure_file(path: Path, label: str, sizes: dict[str, int]) -> None:
    if not path.is_file():
        return
    with suppress(OSError, UnicodeDecodeError):
        sizes[label] = len(path.read_text(encoding="utf-8"))
