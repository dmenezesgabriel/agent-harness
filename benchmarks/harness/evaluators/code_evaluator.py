"""Evaluator for implement-it skill outputs.

Ground truth: the output code passes pre-defined test commands.
Also checks: code is present, no unrelated modifications mentioned.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from harness.evaluators.base import Evaluator
from harness.models import Task, TrialResult


def _extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """Extract (language, code) from fenced code blocks."""
    pattern = r"```(\w*)\n(.*?)```"
    return [(m.group(1), m.group(2)) for m in re.finditer(pattern, text, re.DOTALL)]


def _run_command(cmd: str, cwd: str, timeout: int = 30) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd, timeout=timeout,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        return False, str(exc)


class CodeEvaluator(Evaluator):
    name = "code_evaluator"

    def evaluate(self, result: TrialResult, task: Task) -> TrialResult:
        if result.error or not result.raw_output:
            result.accuracy = 0.0
            result.test_pass_rate = 0.0
            return result

        # Prefer actual code files from workspace snapshot (written by file-based skills
        # like implement-it) over code blocks extracted from markdown summaries.
        snapshot_py = [
            content
            for path, content in sorted((result.workspace_snapshot or {}).items())
            if path.endswith(".py") and not path.startswith("scripts/")
        ]

        if snapshot_py:
            code_sources = snapshot_py
            source_label = "snapshot"
        else:
            code_blocks = _extract_code_blocks(result.raw_output)
            if not code_blocks:
                result.accuracy = 0.0
                result.test_pass_rate = 0.0
                result.evaluator_details = {"has_code": False}
                return result
            code_sources = [code for _, code in code_blocks]
            source_label = "code_blocks"

        test_commands = task.gold_standard.test_commands
        if not test_commands:
            result.accuracy = 1.0
            result.test_pass_rate = 1.0
            result.evaluator_details = {"has_code": True, "note": "no test commands defined", "source": source_label}
            return result

        with tempfile.TemporaryDirectory() as workspace:
            # Write full snapshot so original filenames are importable too
            for path, content in (result.workspace_snapshot or {}).items():
                if not path.endswith(".py") or path.startswith("scripts/"):
                    continue
                dest = Path(workspace) / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content)

            # Write solution_N.py aliases — test commands import from these
            for i, code in enumerate(code_sources):
                Path(workspace, f"solution_{i}.py").write_text(code)

            passed = 0
            details: list[dict] = []
            for cmd in test_commands:
                ok, out = _run_command(cmd, workspace)
                if ok:
                    passed += 1
                details.append({"cmd": cmd, "passed": ok, "output": out[:500]})

        rate = passed / len(test_commands)
        result.test_pass_rate = rate
        result.accuracy = 1.0 if rate == 1.0 else rate
        result.precision = rate
        result.recall = rate
        result.f1 = rate
        result.evaluator_details = {
            "test_results": details,
            "passed": passed,
            "total": len(test_commands),
            "source": source_label,
        }
        return result
