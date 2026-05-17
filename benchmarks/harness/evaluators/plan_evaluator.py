"""Evaluator for plan-it skill outputs.

Scores a plan on:
- Structural completeness (required sections present and non-empty)
- HITL/AFK classification present
- Acceptance criteria presence
- Test type selection noted
- Overall quality_score (0–10 weighted composite)
"""
from __future__ import annotations

from harness.evaluators.base import Evaluator
from harness.evaluators.metrics import precision, recall, f1, section_present
from harness.models import Task, TrialResult

_REQUIRED_SECTIONS = [
    "Context",
    "Use Cases",
    "Requirements",
    "Acceptance Criteria",
    "Tests",
]

_QUALITY_WEIGHTS = {
    "completeness": 0.40,
    "acceptance_criteria_testable": 0.25,
    "classification_present": 0.20,
    "no_empty_required": 0.15,
}


def _score_completeness(text: str, required: list[str]) -> tuple[int, int, int]:
    """Return (tp, fp, fn) treating each required section as a 'finding'."""
    tp = sum(1 for s in required if section_present(text, s))
    fn = len(required) - tp
    fp = 0  # hallucinated sections don't hurt precision for plan eval
    return tp, fp, fn


def _has_classification(text: str) -> bool:
    text_lower = text.lower()
    return ("afk" in text_lower or "hitl" in text_lower or
            "autonomous" in text_lower or "human-in-the-loop" in text_lower)


def _has_testable_criteria(text: str) -> bool:
    """Rough check: acceptance criteria contain binary verifiable language."""
    keywords = ["must", "should", "returns", "produces", "passes", "fails",
                "given", "when", "then", "assert"]
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower) >= 3


class PlanEvaluator(Evaluator):
    name = "plan_evaluator"

    def evaluate(self, result: TrialResult, task: Task) -> TrialResult:
        if result.error or not result.raw_output:
            result.accuracy = 0.0
            result.quality_score = 0.0
            return result

        required = task.gold_standard.required_sections or _REQUIRED_SECTIONS
        tp, fp, fn = _score_completeness(result.raw_output, required)

        result.precision = precision(tp, fp)
        result.recall = recall(tp, fn)
        result.f1 = f1(result.precision, result.recall)

        all_present = fn == 0
        result.accuracy = 1.0 if all_present else tp / len(required)

        has_classify = _has_classification(result.raw_output)
        has_criteria = _has_testable_criteria(result.raw_output)

        completeness_score = result.recall
        classify_score = 1.0 if has_classify else 0.0
        criteria_score = 1.0 if has_criteria else 0.0
        no_empty_score = 1.0 if all_present else result.recall

        result.quality_score = 10.0 * (
            _QUALITY_WEIGHTS["completeness"] * completeness_score
            + _QUALITY_WEIGHTS["acceptance_criteria_testable"] * criteria_score
            + _QUALITY_WEIGHTS["classification_present"] * classify_score
            + _QUALITY_WEIGHTS["no_empty_required"] * no_empty_score
        )

        result.evaluator_details = {
            "sections_found": tp,
            "sections_missing": fn,
            "has_classification": has_classify,
            "has_testable_criteria": has_criteria,
        }
        return result
