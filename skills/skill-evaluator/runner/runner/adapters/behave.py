from __future__ import annotations

import json
import os
import subprocess  # nosec B404
import sys
import tempfile
import time
from pathlib import Path

import structlog

_log = structlog.get_logger()
from typing import Literal

from runner.models import ScenarioResult

_STRUCTURAL_FAILURE_PREVIEW_CHARS = 120


class BehaveStructuralRunner:
    """Run behave structural checks against golden and live artifacts.

    Usage:
        results = BehaveStructuralRunner().run(evals_dir, live_dir)
    """

    def run(self, evals_dir: Path, artifacts_dir: Path) -> list[ScenarioResult]:
        static_dir = evals_dir / "fixtures"
        results = self._behave_pass(evals_dir, static_dir, tag="golden")
        if artifacts_dir != static_dir:
            results += self._behave_pass(evals_dir, artifacts_dir, tag="generated")
        self._print_summary(results)
        return results

    def _behave_pass(
        self, evals_dir: Path, artifacts_dir: Path, tag: str
    ) -> list[ScenarioResult]:
        env = {**os.environ, "EVAL_ARTIFACTS_DIR": str(artifacts_dir)}
        with tempfile.TemporaryDirectory(prefix="behave-result-") as tmp_dir:
            result_file = Path(tmp_dir) / "results.json"
            _log.info("behave_start", tag=tag)
            t0 = time.monotonic()
            proc = self._run_process(evals_dir, tag, result_file, env)
            _log.info("behave_done", tag=tag, elapsed_s=round(time.monotonic() - t0, 1))
            return self.read_results(result_file, proc, tag)

    def _run_process(
        self, evals_dir: Path, tag: str, result_file: Path, env: dict[str, str]
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

    def read_results(
        self, result_file: Path, proc: subprocess.CompletedProcess[str], tag: str
    ) -> list[ScenarioResult]:
        try:
            return _parse_behave_results(result_file)
        except (FileNotFoundError, json.JSONDecodeError):
            return [
                ScenarioResult(
                    feature="unknown",
                    scenario=f"behave ({tag})",
                    status="failed",
                    failure=proc.stderr or proc.stdout,
                )
            ]

    def _print_summary(self, results: list[ScenarioResult]) -> None:
        active = [scenario for scenario in results if scenario.status != "skipped"]
        print(_summary_line(active, len(results) - len(active)))
        for scenario in active:
            _print_scenario_summary(scenario)


def _summary_line(active: list[ScenarioResult], skipped: int) -> str:
    passed = sum(1 for scenario in active if scenario.status == "passed")
    failed = sum(1 for scenario in active if scenario.status == "failed")
    skip_note = f", {skipped} skipped" if skipped else ""
    return f"\n  Structural: {passed} passed, {failed} failed{skip_note}"


def _print_scenario_summary(scenario: ScenarioResult) -> None:
    icon = "PASS" if scenario.status == "passed" else "FAIL"
    print(f"    {icon} {scenario.scenario}")
    if scenario.failure:
        print(f"      {scenario.failure[:_STRUCTURAL_FAILURE_PREVIEW_CHARS]}")


def _parse_behave_results(result_file: Path) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
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
                    failure=_scenario_failure(scenario) if status == "failed" else None,
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
            return str(result.get("error_message", "no error message"))
    return None
