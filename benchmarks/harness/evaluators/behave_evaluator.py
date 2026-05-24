"""Behavioral assertions via Gherkin/behave.

Reconstructs the agent's workspace snapshot into a temp directory, then runs
the skill's .feature file using behave. Pass/fail per scenario is parsed from
behave's JSON formatter output.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from harness.evaluators.base import Evaluator
from harness.models import Task, TaskResult

_FEATURES_DIR = Path(__file__).parent.parent.parent / "features"


class BehaveEvaluator(Evaluator):
    """Run Gherkin feature assertions against a workspace snapshot."""

    name = "behave"

    def __init__(self, features_dir: Path | None = None):
        self._features_dir = features_dir or _FEATURES_DIR

    def evaluate(self, result: TaskResult, task: Task | None = None) -> TaskResult:
        feature_file = self._features_dir / f"{result.skill}.feature"
        if not feature_file.exists():
            return result

        with tempfile.TemporaryDirectory(prefix="bench-behave-") as tmp:
            workspace = Path(tmp)
            self._reconstruct_workspace(workspace, result.workspace_snapshot)

            scenarios, pass_rate = self._run_behave(feature_file, workspace)
            result.behave_scenarios = scenarios
            result.behave_pass_rate = pass_rate

        return result

    # ── private ───────────────────────────────────────────────────────────────

    def _reconstruct_workspace(
        self, workspace: Path, snapshot: dict[str, str]
    ) -> None:
        for rel_path, content in snapshot.items():
            dest = workspace / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_text(content, errors="replace")
            except OSError:
                pass

    def _run_behave(
        self, feature_file: Path, workspace: Path
    ) -> tuple[dict[str, bool], float]:
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as json_out:
            json_path = Path(json_out.name)

        try:
            subprocess.run(
                [
                    sys.executable, "-m", "behave",
                    str(feature_file),
                    "--define", f"workspace={workspace}",
                    "--format", "json",
                    "--outfile", str(json_path),
                    "--no-capture",
                    "--no-capture-stderr",
                    "--no-skipped",
                ],
                capture_output=True,
                text=True,
                cwd=str(self._features_dir.parent),
            )
            scenarios = self._parse_json(json_path)
        finally:
            json_path.unlink(missing_ok=True)

        if not scenarios:
            return {}, 0.0
        pass_rate = sum(scenarios.values()) / len(scenarios)
        return scenarios, pass_rate

    def _parse_json(self, json_path: Path) -> dict[str, bool]:
        try:
            raw = json_path.read_text(errors="replace")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return {}

        scenarios: dict[str, bool] = {}
        for feature in data:
            for element in feature.get("elements", []):
                kw = element.get("keyword", "")
                if kw not in ("Scenario", "Scenario Outline"):
                    continue
                name = element.get("name", "unnamed")
                status = element.get("status", "failed")
                scenarios[name] = status == "passed"
        return scenarios
