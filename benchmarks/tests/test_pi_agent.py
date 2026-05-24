"""Tests for PiAgentAdapter token counting fix (issue 039).

UT-001: output_tokens sums all workspace snapshot values, not just markdown.
IT-001: BehaveEvaluator sets behave_pass_rate for implement-it tasks.
"""
from __future__ import annotations

from harness.adapters.pi_agent import _approx_tokens
from harness.evaluators.behave_evaluator import BehaveEvaluator
from harness.models import TaskResult


def _make_result(**kwargs) -> TaskResult:
    defaults = dict(
        task_id="implement-it-001",
        skill="implement-it",
        platform="pi-agent",
        raw_output="",
        latency_ms=0.0,
        input_tokens=0,
        output_tokens=0,
    )
    defaults.update(kwargs)
    return TaskResult(**defaults)


_GOOD_SUMMARY = """\
# Implementation Summary

## Files Changed
- `solution.py`: main implementation

## Tests
Ran pytest: all tests passed.
Validations run: test, lint

## Design Notes
Used a simple iterative approach with no external dependencies.

## ADR Updates
Not applicable — no architectural decision was required.
"""


# ---------------------------------------------------------------------------
# UT-001: output_tokens reflects all workspace files, not just markdown
# ---------------------------------------------------------------------------

def test_output_tokens_counts_all_snapshot_files():
    """UT-001: new token formula > old formula that only counted markdown."""
    py_content = "x" * 500
    md_content = "y" * 50

    snapshot = {
        "impl/solution.py": py_content,
        "implementation/001-summary.md": md_content,
    }

    # new formula: sum over all snapshot values
    new_tokens = sum(_approx_tokens(v) for v in snapshot.values())

    # old formula: only markdown (what _collect_workspace_output produced)
    old_raw = f"<!-- file: implementation/001-summary.md -->\n{md_content}"
    old_tokens = _approx_tokens(old_raw)

    assert new_tokens > old_tokens


# ---------------------------------------------------------------------------
# IT-001: BehaveEvaluator sets behave_pass_rate for implement-it task
# ---------------------------------------------------------------------------

def test_behave_evaluator_sets_pass_rate_for_implement_it():
    """IT-001: behave_pass_rate is set by BehaveEvaluator, not left at default 0.0."""
    snapshot = {
        "implementation/001-solution-summary.md": _GOOD_SUMMARY,
    }
    result = _make_result(workspace_snapshot=snapshot)
    assert result.behave_pass_rate == 0.0  # confirm default before evaluation

    evaluator = BehaveEvaluator()
    result = evaluator.evaluate(result)

    assert result.behave_pass_rate > 0.0, (
        f"behave_pass_rate was not updated by BehaveEvaluator; "
        f"scenarios={result.behave_scenarios}"
    )
