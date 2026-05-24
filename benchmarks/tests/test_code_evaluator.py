"""Tests for CodeEvaluator metrics fix (task 031).

Covers UT-001, UT-002, and IT-001.
"""
from __future__ import annotations

import pytest

from harness.evaluators.code_evaluator import CodeEvaluator, _extract_code_blocks
from harness.evaluators.metrics import mean_std
from harness.models import GoldStandard, Task, TaskResult


# ======================================================================
# UT-001: precision/recall/f1 are not copies of test_pass_rate
# ======================================================================

def test_code_evaluator_omits_redundant_metrics():
    """UT-001: CodeEvaluator does not set precision/recall/f1 to test_pass_rate."""
    task = Task(
        id="impl-001",
        skill="implement-it",
        title="Test",
        instruction="Write a function that returns 42",
        evaluator="code",
        gold_standard=GoldStandard(
            test_commands=[
                "python3 -c \"assert 1 + 1 == 2\"",
                "python3 -c \"assert 2 + 2 == 4\"",
                "python3 -c \"assert 3 + 3 == 6\"",
                "python3 -c \"assert 4 + 4 == 8\"",
            ],
        ),
    )
    result = TaskResult(
        task_id="impl-001",
        skill="implement-it",
        platform="opencode",
        raw_output="```python\ndef fn():\n    return 42\n```",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )

    evaluator = CodeEvaluator()
    evaluated = evaluator.evaluate(result, task)

    # test_pass_rate should be 1.0 (all 4 commands use python3, available in env)
    assert evaluated.test_pass_rate == 1.0

    # precision/recall/f1 must not equal test_pass_rate (they remain at default 0.0)
    assert evaluated.precision != evaluated.test_pass_rate
    assert evaluated.recall != evaluated.test_pass_rate
    assert evaluated.f1 != evaluated.test_pass_rate
    assert evaluated.precision == 0.0
    assert evaluated.recall == 0.0
    assert evaluated.f1 == 0.0

    # evaluator_details should include the note
    assert "note" in evaluated.evaluator_details
    assert "not computed" in evaluated.evaluator_details["note"]


def test_code_evaluator_early_return_also_omits_metrics():
    """Early return paths (error, no code) also leave precision/recall/f1 at 0.0."""
    task = Task(
        id="impl-001",
        skill="implement-it",
        title="Test",
        instruction="Write code",
        evaluator="code",
    )

    # Error case
    result = TaskResult(
        task_id="impl-001",
        skill="implement-it",
        platform="opencode",
        raw_output="",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        error="Agent crashed",
    )
    evaluator = CodeEvaluator()
    evaluated = evaluator.evaluate(result, task)
    assert evaluated.precision == 0.0
    assert evaluated.recall == 0.0
    assert evaluated.f1 == 0.0
    assert evaluated.test_pass_rate == 0.0

    # No code blocks case
    result2 = TaskResult(
        task_id="impl-001",
        skill="implement-it",
        platform="opencode",
        raw_output="Just some text without code blocks",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )
    evaluated2 = evaluator.evaluate(result2, task)
    assert evaluated2.precision == 0.0
    assert evaluated2.recall == 0.0
    assert evaluated2.f1 == 0.0
    assert evaluated2.test_pass_rate == 0.0


# ======================================================================
# UT-002: Zero-value precision/recall/f1 don't crash mean_std aggregation
# ======================================================================

def test_mean_std_with_zero_values():
    """UT-002: mean_std aggregation handles zero-value precision/recall/f1 lists."""
    values = [0.0, 0.0, 0.0, 0.0, 0.0]
    mean, std = mean_std(values)
    assert mean == 0.0
    assert std == 0.0


def test_mean_std_with_empty_list():
    """UT-002: mean_std handles empty lists gracefully."""
    mean, std = mean_std([])
    assert mean == 0.0
    assert std == 0.0


def test_mean_std_with_mixed_values():
    """UT-002: mean_std works normally with non-zero values mixed with zeros."""
    values = [0.0, 0.0, 0.75, 0.0, 1.0]
    mean, std = mean_std(values)
    assert mean == 0.35
    assert std > 0.0


# ======================================================================
# IT-001: Integration — benchmark-mimicking run with code evaluator
# ======================================================================

def test_integration_code_evaluator_metrics_not_redundant():
    """IT-001: Full evaluator run with implement-it style task leaves precision/recall/f1 at 0.0."""
    task = Task(
        id="impl-002",
        skill="implement-it",
        title="Implement fibonacci",
        instruction="Write a fibonacci function",
        evaluator="code",
        gold_standard=GoldStandard(
            test_commands=[
                "python3 -c \"import sys; sys.path.insert(0, '.'); from solution_0 import fib; assert fib(0) == 0\"",
                "python3 -c \"import sys; sys.path.insert(0, '.'); from solution_0 import fib; assert fib(1) == 1\"",
                "python3 -c \"import sys; sys.path.insert(0, '.'); from solution_0 import fib; assert fib(10) == 55\"",
            ],
        ),
    )
    result = TaskResult(
        task_id="impl-002",
        skill="implement-it",
        platform="opencode",
        raw_output="Agent produced solution_0.py",
        workspace_snapshot={
            "solution_0.py": "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n",
        },
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )

    evaluator = CodeEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.test_pass_rate == 1.0
    assert evaluated.precision == 0.0
    assert evaluated.recall == 0.0
    assert evaluated.f1 == 0.0
    assert evaluated.precision != evaluated.test_pass_rate
    assert "note" in evaluated.evaluator_details
    assert "source" in evaluated.evaluator_details
    assert evaluated.evaluator_details["source"] == "snapshot"


# ======================================================================
# Helper: _extract_code_blocks
# ======================================================================

def test_extract_code_blocks():
    blocks = _extract_code_blocks("```python\nprint('hello')\n```")
    assert len(blocks) == 1
    assert blocks[0][0] == "python"
    assert "print('hello')" in blocks[0][1]


def test_extract_code_blocks_empty():
    assert _extract_code_blocks("no code here") == []
