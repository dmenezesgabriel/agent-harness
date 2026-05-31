#!/usr/bin/env python3
"""Skill evaluator orchestrator.

Discovers skills/*/evals/, invokes the skill via claude CLI (haiku), runs behave
for structural checks on live output, and optionally runs LLM-as-judge (sonnet)
on golden fixtures for qualitative rubric evaluation.

Usage:
    uv run python -m runner.run [--skill <name>] [--mode invoke|judge|all]
    uv run python -m runner.run --skill plan-it
    uv run python -m runner.run --skill dataviz --mode all
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from contextlib import suppress
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.ports import AgentPort, JudgePort

_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent  # agent-harness/skills/

_MODES = ("invoke", "judge", "all")
_STRUCTURAL_FAILURE_PREVIEW_CHARS = 120
_LARGE_ARTIFACT_CHARS = 15_000
_PERCENT_SCALE = 100
Mode = Literal["invoke", "judge", "all"]


class CliArgs(BaseModel):
    skill: str | None = None
    mode: Mode = "invoke"


class ScenarioResult(BaseModel):
    feature: str
    scenario: str
    status: Literal["passed", "failed", "skipped"]
    failure: str | None = None


class JudgeReport(BaseModel):
    rubric_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class RubricDefinition(BaseModel):
    id: str
    artifact_file: str
    prompt: str
    artifact_section: str | None = None


class RubricFile(BaseModel):
    rubrics: list[RubricDefinition] = Field(default_factory=list)


def main() -> None:
    args = _parse_args()
    skill_dirs = _discover_skills(args.skill)
    if not skill_dirs:
        print(f"No evals found under {_SKILLS_ROOT}", file=sys.stderr)
        sys.exit(1)

    adapter: AgentPort | None = (
        ClaudeCodeAdapter(skill_root=_SKILLS_ROOT)
        if args.mode in ("invoke", "all")
        else None
    )
    judge: JudgePort | None = (
        ClaudeCodeAdapter(skill_root=_SKILLS_ROOT)
        if args.mode in ("judge", "all")
        else None
    )

    overall_ok = True
    for skill_dir in skill_dirs:
        ok = _evaluate_skill(skill_dir, args.mode, adapter, judge)
        overall_ok = overall_ok and ok

    sys.exit(0 if overall_ok else 1)


# ── skill discovery ───────────────────────────────────────────────────────────


def _discover_skills(skill_filter: str | None) -> list[Path]:
    dirs: list[Path] = []
    for evals_dir in sorted(_SKILLS_ROOT.glob("*/evals")):
        if (
            evals_dir.is_dir()
            and evals_dir.parent.name != "skill-evaluator"
            and (skill_filter is None or evals_dir.parent.name == skill_filter)
        ):
            dirs.append(evals_dir)
    return dirs


# ── per-skill evaluation ──────────────────────────────────────────────────────


def _evaluate_skill(
    evals_dir: Path,
    mode: Mode,
    adapter: AgentPort | None,
    judge: JudgePort | None,
) -> bool:
    skill_name = evals_dir.parent.name
    print(f"\n{'=' * 60}")
    print(f"Evaluating skill: {skill_name}  (mode: {mode})")
    print(f"{'=' * 60}")

    # golden fixtures dir — used by judge; overwritten by _invoke_skill for behave
    golden_dir = evals_dir / "fixtures"
    artifacts_dir = golden_dir

    artifact_sizes: dict[str, int] = {}
    structural_results: list[ScenarioResult] = []
    if mode in ("invoke", "all") and adapter is not None:
        artifacts_dir = _invoke_skill(skill_name, evals_dir, adapter)
        artifact_sizes = _measure_artifacts(artifacts_dir)
        structural_results = _run_behave(evals_dir, artifacts_dir)

    judge_verdicts: list[JudgeReport] = []
    if mode in ("judge", "all") and judge is not None:
        judge_verdicts = _run_judge(evals_dir, artifacts_dir, judge)

    report_path = _write_report(
        skill_name, evals_dir, mode, structural_results, judge_verdicts, artifact_sizes
    )
    print(f"\nReport: {report_path}")

    failed_structural = sum(1 for r in structural_results if r.status == "failed")
    failed_judge = sum(1 for v in judge_verdicts if not v.passed)
    return failed_structural == 0 and failed_judge == 0


# ── agent invocation ──────────────────────────────────────────────────────────


def _invoke_skill(skill_name: str, evals_dir: Path, adapter: AgentPort) -> Path:
    input_files = sorted((evals_dir / "fixtures").glob("input_*.md"))
    if not input_files:
        print(
            f"  No input_*.md fixtures found in {evals_dir / 'fixtures'} — skipping invocation"
        )
        return evals_dir / "fixtures"

    live_dir = evals_dir / "fixtures" / "_live"
    _reset_live_dir(live_dir)

    input_text = input_files[0].read_text(encoding="utf-8")
    print(f"  Invoking skill with fixture: {input_files[0].name}")
    artifacts = adapter.invoke_skill(skill_name, input_text)

    for rel_path, content in artifacts.files.items():
        dest = live_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    return live_dir


def _reset_live_dir(live_dir: Path) -> None:
    """Remove stale artifacts from a previous run, then recreate the directory."""
    if live_dir.exists():
        shutil.rmtree(live_dir)
    live_dir.mkdir(parents=True)
    (live_dir / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")


# ── artifact verbosity ────────────────────────────────────────────────────────


def _measure_artifacts(artifacts_dir: Path) -> dict[str, int]:
    """Return {relative_path: char_count} for each file in artifacts_dir.

    Character count is an honest proxy for output verbosity — actual token counts
    are not available via the claude CLI.
    """
    sizes: dict[str, int] = {}
    for path in sorted(artifacts_dir.rglob("*")):
        if not path.is_file():
            continue
        with suppress(OSError, UnicodeDecodeError):
            sizes[str(path.relative_to(artifacts_dir))] = len(
                path.read_text(encoding="utf-8")
            )
    return sizes


# ── behave runner ─────────────────────────────────────────────────────────────


def _run_behave(evals_dir: Path, live_dir: Path) -> list[ScenarioResult]:
    """Run two behave passes: golden (static fixtures) then live (agent output)."""
    static_dir = evals_dir / "fixtures"
    results = _behave_pass(evals_dir, static_dir, tag="golden")
    if live_dir != static_dir:
        results += _behave_pass(evals_dir, live_dir, tag="live")
    _print_structural_summary(results)
    return results


def _behave_pass(
    evals_dir: Path, artifacts_dir: Path, tag: str
) -> list[ScenarioResult]:
    env = {**os.environ, "EVAL_ARTIFACTS_DIR": str(artifacts_dir)}
    with tempfile.TemporaryDirectory(prefix="behave-result-") as tmp_dir:
        result_file = Path(tmp_dir) / "results.json"
        proc = _run_behave_process(evals_dir, tag, result_file, env)
        return _read_behave_results(result_file, proc, tag)


def _run_behave_process(
    evals_dir: Path, tag: str, result_file: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "behave",
        str(evals_dir),
        f"--tags={tag}",
        "--format=json",
        f"--outfile={result_file}",
        "--no-capture",
        "--quiet",
    ]
    return subprocess.run(  # nosec B603
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_behave_results(
    result_file: Path, proc: subprocess.CompletedProcess[str], tag: str
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    try:
        raw: object = json.loads(result_file.read_text(encoding="utf-8"))
        for feature in _as_object_list(raw):
            for scenario in _as_object_list(feature.get("elements", [])):
                if scenario.get("type") == "background":
                    continue
                status = _scenario_status(scenario)
                results.append(
                    ScenarioResult(
                        feature=str(feature.get("name", "unknown")),
                        scenario=str(scenario.get("name", "unknown")),
                        status=status,
                        failure=_scenario_failure(scenario)
                        if status == "failed"
                        else None,
                    )
                )
    except (FileNotFoundError, json.JSONDecodeError):
        results.append(
            ScenarioResult(
                feature="unknown",
                scenario=f"behave ({tag})",
                status="failed",
                failure=proc.stderr or proc.stdout,
            )
        )
    return results


def _as_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _scenario_status(
    scenario: dict[str, object],
) -> Literal["passed", "failed", "skipped"]:
    if scenario.get("status") == "skipped":
        return "skipped"
    for step in _as_object_list(scenario.get("steps", [])):
        result = step.get("result", {})
        if not isinstance(result, dict):
            continue
        if result.get("status") == "failed":
            return "failed"
        if result.get("status") == "skipped":
            return "skipped"
    return "passed"


def _scenario_failure(scenario: dict[str, object]) -> str | None:
    for step in _as_object_list(scenario.get("steps", [])):
        result = step.get("result", {})
        if not isinstance(result, dict):
            continue
        if result.get("status") == "failed":
            error_message = result.get("error_message", "no error message")
            return str(error_message)
    return None


def _print_structural_summary(results: list[ScenarioResult]) -> None:
    active = [r for r in results if r.status != "skipped"]
    passed = sum(1 for r in active if r.status == "passed")
    failed = sum(1 for r in active if r.status == "failed")
    skipped = len(results) - len(active)
    skip_note = f", {skipped} skipped" if skipped else ""
    print(f"\n  Structural: {passed} passed, {failed} failed{skip_note}")
    for r in active:
        icon = "PASS" if r.status == "passed" else "FAIL"
        print(f"    {icon} {r.scenario}")
        if r.failure:
            print(f"      {r.failure[:_STRUCTURAL_FAILURE_PREVIEW_CHARS]}")


# ── judge runner ──────────────────────────────────────────────────────────────


def _run_judge(
    evals_dir: Path, artifacts_dir: Path, judge: JudgePort
) -> list[JudgeReport]:
    rubrics_dir = evals_dir / "rubrics"
    if not rubrics_dir.exists():
        print("  No rubrics/ directory found — skipping judge")
        return []

    primary_chart: Path | None = (
        None  # resolved lazily when _live_primary_ is encountered
    )
    verdicts: list[JudgeReport] = []

    for rubric_file in sorted(rubrics_dir.glob("*.yaml")):
        rubric_data = RubricFile.model_validate(
            yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
        )
        for rubric in rubric_data.rubrics:
            artifact_name = rubric.artifact_file
            if artifact_name == "_live_primary_":
                if primary_chart is None:
                    primary_chart = _find_primary_chart(artifacts_dir)
                if primary_chart is None:
                    print(
                        f"  Rubric {rubric.id!r}: no primary chart artifact found - skipping"
                    )
                    continue
                artifact_file = primary_chart
            else:
                # Static fixtures always resolve from the golden dir, not live output.
                # In `all` mode, artifacts_dir points to _live/ — looking there would
                # silently skip every rubric that references a golden fixture file.
                artifact_file = evals_dir / "fixtures" / artifact_name

            if not artifact_file.exists():
                print(
                    f"  Rubric {rubric.id!r}: fixture {artifact_name!r} not found - skipping"
                )
                continue

            content = artifact_file.read_text(encoding="utf-8")
            if rubric.artifact_section:
                content = _extract_section(content, rubric.artifact_section)

            verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
            verdicts.append(JudgeReport.model_validate(verdict.model_dump()))

    _print_judge_summary(verdicts)
    return verdicts


_VIZ_KEYWORDS_PAT = re.compile(
    r"new\s+Chart\b|Chart\.js"
    r"|plotly|go\.Figure|px\.\w+\("
    r"|alt\.Chart\b|\.mark_line\(\)|\.mark_bar\(\)"
    r"|import\s+matplotlib|plt\.(plot|bar|scatter)\b"
    r'|"mark"\s*:\s*"(?:line|bar|area|point)"'
    r"|d3\.select\b"
    r"|from\s+['\"](?:recharts|victory|echarts|highcharts|apexcharts|@nivo/\w+)['\"]"
    r"|(?:LineChart|BarChart|AreaChart|PieChart|ScatterChart)\b",
    re.IGNORECASE,
)
_VIZ_EXTENSIONS = (".html", ".js", ".jsx", ".tsx", ".py", ".ipynb", ".json")


def _find_primary_chart(artifacts_dir: Path) -> Path | None:
    """Return the first visualization file found in artifacts_dir, by extension priority."""
    for ext in _VIZ_EXTENSIONS:
        candidates = sorted(artifacts_dir.rglob(f"*{ext}"))
        for path in candidates:
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


def _print_judge_summary(verdicts: list[JudgeReport]) -> None:
    passed = sum(1 for v in verdicts if v.passed)
    failed = sum(1 for v in verdicts if not v.passed)
    print(f"\n  Judge: {passed} passed, {failed} failed")
    for v in verdicts:
        icon = "PASS" if v.passed else "FAIL"
        print(f"    {icon} {v.rubric_id} (score={v.score:.2f}): {v.reasoning}")


# ── report writer ─────────────────────────────────────────────────────────────


def _write_report(
    skill_name: str,
    evals_dir: Path,
    mode: Mode,
    structural_results: list[ScenarioResult],
    judge_verdicts: list[JudgeReport],
    artifact_sizes: dict[str, int] | None = None,
) -> Path:
    reports_dir = evals_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    report_path = reports_dir / f"{skill_name}-{today}.md"

    lines = [
        f"# Eval Report: {skill_name}",
        f"Date: {today} | Mode: {mode}",
        "",
    ]

    active_structural = [r for r in structural_results if r.status != "skipped"]
    if active_structural:
        lines += ["## Structural checks (behave)", ""]
        lines.append("| Scenario | Result |")
        lines.append("|----------|--------|")
        for r in active_structural:
            icon = "PASS" if r.status == "passed" else "FAIL"
            lines.append(f"| {r.scenario} | {icon} |")
        failures = [r for r in active_structural if r.status == "failed"]
        if failures:
            lines += ["", "### Failures", ""]
            for r in failures:
                lines.append(f"**{r.scenario}**: {r.failure}")
        lines.append("")

    if judge_verdicts:
        lines += ["## LLM-as-judge checks", ""]
        lines.append("| Rubric | Score | Result | Reasoning |")
        lines.append("|--------|-------|--------|-----------|")
        for v in judge_verdicts:
            icon = "PASS" if v.passed else "FAIL"
            lines.append(f"| {v.rubric_id} | {v.score:.2f} | {icon} | {v.reasoning} |")
        lines.append("")

    if artifact_sizes:
        total_chars = sum(artifact_sizes.values())
        lines += ["## Artifact verbosity (chars — proxy for output size)", ""]
        lines.append("| File | Characters |")
        lines.append("|------|-----------|")
        for rel, size in sorted(artifact_sizes.items()):
            flag = " ⚠ large" if size > _LARGE_ARTIFACT_CHARS else ""
            lines.append(f"| {rel} | {size:,}{flag} |")
        lines.append(f"| **Total** | **{total_chars:,}** |")
        lines.append("")

    s_pass = sum(1 for r in active_structural if r.status == "passed")
    j_pass = sum(1 for v in judge_verdicts if v.passed)
    total_checks = len(active_structural) + len(judge_verdicts)
    total_pass = s_pass + j_pass
    if total_checks:
        pct = int(_PERCENT_SCALE * total_pass / total_checks)
        lines.append(f"**Pass rate**: {total_pass}/{total_checks} ({pct}%)")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ── arg parsing ───────────────────────────────────────────────────────────────


def _parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="Evaluate agent-harness skills")
    parser.add_argument("--skill", help="Skill name to evaluate (default: all)")
    parser.add_argument(
        "--mode",
        choices=_MODES,
        default="invoke",
        help="Evaluation mode (default: invoke)",
    )
    return CliArgs.model_validate(vars(parser.parse_args()))


if __name__ == "__main__":
    main()
