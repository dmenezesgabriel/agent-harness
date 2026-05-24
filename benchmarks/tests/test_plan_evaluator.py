"""Unit and integration tests for PlanEvaluator workspace/metrics fixes.

Covers UT-001 through UT-003 and IT-001 from task 030.
"""
from __future__ import annotations

import pytest

from harness.evaluators.metrics import section_present
from harness.evaluators.plan_evaluator import (
    PlanEvaluator,
    _ac_keyword_density,
    _ac_section_body,
    _all_present_sections,
    _count_list_items,
    _has_classification,
    _merge_content,
    _score_completeness,
)
from harness.models import GoldStandard, Task, TaskResult


# ======================================================================
# UT-001: Merge raw_output + workspace_snapshot and verify sections found
# ======================================================================

def test_merge_sections_from_both_sources():
    """UT-001: Sections found from both raw_output and workspace_snapshot."""
    raw = "## Some intro\n\nnothing useful here\n"
    ws = {
        "docs/plan.md": (
            "## Context\n\nThis is the context for the rate limiter feature.\n\n"
            "## Requirements\n\nMust implement a token bucket algorithm.\n\n"
            "## Acceptance Criteria\n\nGiven a request, when over limit, then return 429.\n\n"
            "## Tests\n\nTest basic consume and capacity cap scenarios."
        ),
    }
    merged, source = _merge_content(raw, ws)
    assert source == "both"

    required = ["Context", "Requirements", "Acceptance Criteria", "Tests"]
    tp, fp, fn = _score_completeness(merged, required)
    assert tp == len(required), f"Expected tp={len(required)}, got tp={tp}"
    assert fn == 0


def test_merge_sections_workspace_only():
    """Workspace-only content still finds sections."""
    ws = {
        "plan.md": (
            "## Context\n\nThis feature requires background processing support.\n\n"
            "## Requirements\n\nImplement async job queue with retry logic."
        ),
    }
    merged, source = _merge_content("", ws)
    assert source == "workspace_snapshot"

    required = ["Context", "Requirements"]
    tp, fp, fn = _score_completeness(merged, required)
    assert tp == 2
    assert fn == 0


# ======================================================================
# UT-002: Precision with known false positives
# ======================================================================

def test_precision_drops_with_extra_sections():
    """UT-002: fp > 0 when extra sections are present, precision < 1.0."""
    text = (
        "## Context\n\nThis is context for the background jobs feature.\n\n"
        "## Requirements\n\nMust implement a token bucket algorithm for rate limiting.\n\n"
        "## Random Extra\n\nThis section is not in the gold standard at all.\n\n"
        "## Another Extra\n\nAlso not required by the gold standard specification.\n\n"
        "## Acceptance Criteria\n\nGiven an authenticated request, when limit is exceeded, then 429.\n\n"
        "## Tests\n\nTest basic consume and capacity cap with thread safety scenarios."
    )
    required = ["Context", "Requirements", "Acceptance Criteria", "Tests"]
    tp, fp, fn = _score_completeness(text, required)
    assert tp == 4
    assert fp >= 1
    assert fn == 0

    from harness.evaluators.metrics import precision
    p = precision(tp, fp)
    assert p < 1.0


def test_no_extra_sections_precision_one():
    """When no extra sections, precision = 1.0."""
    text = (
        "## Context\n\nThis is context for the background jobs feature.\n\n"
        "## Requirements\n\nMust implement a token bucket algorithm for rate limiting.\n\n"
        "## Acceptance Criteria\n\nGiven an authenticated request, when limit exceeded, 429.\n\n"
        "## Tests\n\nTest basic consume and capacity cap with thread safety scenarios."
    )
    required = ["Context", "Requirements", "Acceptance Criteria", "Tests"]
    tp, fp, fn = _score_completeness(text, required)
    assert fp == 0

    from harness.evaluators.metrics import precision
    p = precision(tp, fp)
    assert p == 1.0


# ======================================================================
# UT-003: Classification keywords case-insensitive
# ======================================================================

@pytest.mark.parametrize("keyword", ["AFK", "afk", "Afk", "HITL", "hitl", "Hitl"])
def test_classification_matches_case_variants(keyword):
    """UT-003: _has_classification matches AFK/HITL regardless of case."""
    text = f"## Classification\n\nThis task is {keyword}."
    assert _has_classification(text)


def test_classification_matches_autonomous():
    assert _has_classification("## Classification\n\nautonomous system")


def test_classification_matches_human_in_the_loop():
    assert _has_classification("## Classification\n\nhuman-in-the-loop")


def test_classification_no_match():
    assert not _has_classification("## Some heading\n\nnothing about classification.")


# ======================================================================
# IT-001: End-to-end with simulated file-writing agent
# ======================================================================

def test_evaluate_finds_sections_in_workspace_files():
    """IT-001: PlanEvaluator.evaluate() finds sections in workspace files with empty raw_output."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
        gold_standard=GoldStandard(required_sections=[
            "Context", "Requirements", "Acceptance Criteria", "Tests",
        ]),
    )
    # Simulate TaskResult with workspace files but empty raw_output
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="opencode",
        raw_output="I have planned the feature.",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        workspace_snapshot={
            "docs/adr-001.md": (
                "## Context\n\nThe API needs rate limiting to prevent abuse.\n\n"
                "## Requirements\n\nImplement token bucket algorithm with configurable rate.\n\n"
                "## Acceptance Criteria\n\nGiven an API key, when over limit, then return 429.\n\n"
                "## Tests\n\nTest basic consume, capacity cap, and concurrent access scenarios."
            ),
        },
    )

    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.accuracy > 0.0
    assert evaluated.evaluator_details["sections_found"] > 0
    assert evaluated.evaluator_details["content_source"] == "both"
    assert evaluated.precision == 0.0
    assert evaluated.recall == 0.0
    assert evaluated.f1 == 0.0


def test_evaluate_falls_back_to_raw_output_when_no_workspace():
    """AC-003: Empty workspace_snapshot falls back to raw_output only."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
        gold_standard=GoldStandard(required_sections=[
            "Context", "Requirements", "Acceptance Criteria", "Tests",
        ]),
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="claude-code",
        raw_output=(
            "## Context\n\nThis feature adds background job processing support.\n\n"
            "## Requirements\n\nMust implement async queue with configurable retry policy.\n\n"
            "## Acceptance Criteria\n\nGiven a job, when it fails, then retry up to N times.\n\n"
            "## Tests\n\nTest enqueue, dequeue, retry, and failure scenarios end-to-end."
        ),
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        workspace_snapshot={},
    )

    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.accuracy > 0.0
    assert evaluated.evaluator_details["content_source"] == "raw_output"
    assert evaluated.evaluator_details["sections_found"] == 4


def test_evaluate_no_crash_on_empty_both():
    """Graceful handling when both raw_output and workspace_snapshot are empty."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="opencode",
        raw_output="",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        workspace_snapshot={},
    )

    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.accuracy == 0.0
    assert evaluated.quality_score == 0.0


def test_evaluate_handles_error():
    """When result.error is set, return zero metrics."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="opencode",
        raw_output="Some output",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        error="Agent crashed",
    )

    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.accuracy == 0.0
    assert evaluated.quality_score == 0.0


def test_evaluate_precision_reflects_false_positives():
    """AC-002: Extra sections produce fp > 0 and precision < 1.0."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
        gold_standard=GoldStandard(required_sections=[
            "Context", "Requirements", "Acceptance Criteria", "Tests",
        ]),
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="opencode",
        raw_output="",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
        workspace_snapshot={
            "docs/plan.md": (
                "## Context\n\nThis feature adds background job processing support.\n\n"
                "## Requirements\n\nMust implement async queue with configurable retry policy.\n\n"
                "## Acceptance Criteria\n\nGiven a job, when it fails, then retry up to N times.\n\n"
                "## Tests\n\nTest enqueue, dequeue, retry, and failure scenarios end-to-end.\n\n"
                "## Implementation Details\n\nUse Redis-backed queue with exponential backoff.\n\n"
                "## Deployment Plan\n\nDeploy as a separate worker process with autoscaling."
            ),
        },
    )

    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)

    assert evaluated.evaluator_details["sections_extra"] > 0
    assert evaluated.precision == 0.0


def test_has_classification_afk_uppercase():
    """AC-004: _has_classification returns True for uppercase AFK."""
    assert _has_classification("## HITL Decision Point\n\nNeeds human review.")


# ======================================================================
# New: filler rejection and AC-scoped checks
# ======================================================================

def test_section_present_rejects_filler():
    """section_present returns False when section body is only a filler phrase."""
    from harness.evaluators.metrics import section_present
    text = "## Acceptance Criteria\n\nN/A\n\n## Requirements\n\nImplement token bucket."
    assert not section_present(text, "Acceptance Criteria")


def test_section_present_rejects_tbd():
    from harness.evaluators.metrics import section_present
    text = "## Tests\n\nTBD\n\n## Context\n\nSome context about the feature design."
    assert not section_present(text, "Tests")


def test_section_present_short_non_filler_still_passes():
    """Short content that is not a known filler phrase is allowed."""
    from harness.evaluators.metrics import section_present
    text = "## Context\n\nShort but real.\n\n## Requirements\n\nImplement async queue with retry."
    # "Short but real." is only 15 chars but is not a filler — should pass
    assert section_present(text, "Context")


def test_section_present_accepts_substantive_content():
    from harness.evaluators.metrics import section_present
    text = "## Context\n\nThis feature adds background job processing to the platform.\n"
    assert section_present(text, "Context")


def test_ac_keyword_density_scoped_to_ac_section():
    """ac_keyword_density only scores keywords in the AC section, not the full doc."""
    # Requirements section has all the keywords, but AC section is empty filler
    full_doc = (
        "## Requirements\n\nMust implement, should return, given request, when valid, "
        "then assert passes, verify produces correct result.\n\n"
        "## Acceptance Criteria\n\nN/A\n"
    )
    ac_body = _ac_section_body(full_doc)
    density = _ac_keyword_density(ac_body)
    assert density == 0.0, "Keywords in Requirements should not boost AC density"


def test_ac_keyword_density_scores_ac_content():
    ac_body = "- Given a request, when rate exceeded, then must return 429.\n- Should verify token count."
    density = _ac_keyword_density(ac_body)
    assert density > 0.0


def test_count_list_items():
    text = "- item one\n- item two\n* item three\n1. numbered\n2. also numbered\nplain text"
    assert _count_list_items(text) == 5


def test_quality_score_zero_for_filler_sections():
    """A plan with all required sections but filler content scores near 0."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
        gold_standard=GoldStandard(required_sections=[
            "Context", "Requirements", "Acceptance Criteria", "Tests",
        ]),
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="claude-code",
        raw_output=(
            "## Context\n\nN/A\n\n"
            "## Requirements\n\nTBD\n\n"
            "## Acceptance Criteria\n\nTODO\n\n"
            "## Tests\n\nSee above\n"
        ),
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )
    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)
    assert evaluated.accuracy == 0.0
    assert evaluated.quality_score == 0.0


# ======================================================================
# UT-003 (036): PlanEvaluator leaves precision, recall, f1 at 0.0
# ======================================================================

def test_plan_evaluator_does_not_set_precision_recall_f1():
    """UT-003: PlanEvaluator.evaluate() never writes precision, recall, or f1."""
    task = Task(
        id="plan-it-001",
        skill="plan-it",
        title="Test",
        instruction="Do X",
        evaluator="plan",
        gold_standard=GoldStandard(required_sections=["Context", "Requirements"]),
    )
    result = TaskResult(
        task_id="plan-it-001",
        skill="plan-it",
        platform="claude-code",
        raw_output=(
            "## Context\n\nThis is the context.\n\n"
            "## Requirements\n\nMust implement X."
        ),
        latency_ms=50.0,
        input_tokens=10,
        output_tokens=5,
    )
    evaluator = PlanEvaluator()
    evaluated = evaluator.evaluate(result, task)
    assert evaluated.precision == 0.0
    assert evaluated.recall == 0.0
    assert evaluated.f1 == 0.0
    assert evaluated.accuracy > 0.0
