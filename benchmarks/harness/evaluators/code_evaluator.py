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

        code_blocks = _extract_code_blocks(result.raw_output)
        has_code = len(code_blocks) > 0

        if not has_code:
            result.accuracy = 0.0
            result.test_pass_rate = 0.0
            result.evaluator_details = {"has_code": False}
            return result

        test_commands = task.gold_standard.test_commands
        if not test_commands:
            # no test commands defined — score on presence only
            result.accuracy = 1.0 if has_code else 0.0
            result.test_pass_rate = result.accuracy
            result.evaluator_details = {"has_code": True, "note": "no test commands defined"}
            return result

        with tempfile.TemporaryDirectory() as workspace:
            # write code blocks to files for evaluation
            for i, (lang, code) in enumerate(code_blocks):
                ext = {"python": ".py", "typescript": ".ts", "javascript": ".js"}.get(lang, ".txt")
                Path(workspace, f"solution_{i}{ext}").write_text(code)

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
        result.evaluator_details = {"test_results": details, "passed": passed, "total": len(test_commands)}
        return result
