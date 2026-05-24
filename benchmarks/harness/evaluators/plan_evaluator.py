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
from harness.evaluators.metrics import extract_section, section_present
from harness.models import Task, TaskResult

_REQUIRED_SECTIONS = [
    "Context",
    "Use Cases",
    "Requirements",
    "Acceptance Criteria",
    "Tests",
]

_QUALITY_WEIGHTS = {
    "completeness": 0.40,
    "acceptance_criteria_density": 0.25,
    "classification_present": 0.20,
    "criteria_item_count": 0.15,
}


def _all_present_sections(text: str) -> set[str]:
    """Return set of markdown heading texts that have non-empty content."""
    sections = set()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#"):
            heading_text = line.lstrip("#").strip()
            has_content = False
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith("#"):
                    break
                if next_line:
                    has_content = True
                    break
                j += 1
            if has_content and heading_text:
                sections.add(heading_text)
        i += 1
    return sections


def _score_completeness(text: str, required: list[str]) -> tuple[int, int, int]:
    """Return (tp, fp, fn) treating each section as a 'finding'.

    tp: required sections present in the output
    fp: present headings that don't match any required section
    fn: required sections missing from the output
    """
    tp = sum(1 for s in required if section_present(text, s))
    fn = len(required) - tp

    present_headings = _all_present_sections(text)
    fp = sum(
        1 for h in present_headings
        if not any(req.lower() in h.lower() for req in required)
    )

    return tp, fp, fn


def _merge_content(
    raw_output: str,
    workspace_snapshot: dict[str, str] | None,
) -> tuple[str, str]:
    """Merge raw_output and workspace_snapshot into a single text for evaluation.

    Returns (merged_text, source_label) where source_label is one of
    "raw_output", "workspace_snapshot", or "both".
    """
    has_raw = bool(raw_output and raw_output.strip())
    has_ws = bool(workspace_snapshot)

    if has_raw and has_ws:
        parts = [raw_output]
        for path, content in workspace_snapshot.items():
            if content and content.strip():
                parts.append(f"<!-- File: {path} -->\n\n{content}")
        return "\n\n".join(parts), "both"
    elif has_raw:
        return raw_output, "raw_output"
    elif has_ws:
        parts = []
        for path, content in workspace_snapshot.items():
            if content and content.strip():
                parts.append(f"<!-- File: {path} -->\n\n{content}")
        return "\n\n".join(parts), "workspace_snapshot"
    else:
        return "", "none"


_AC_ALIASES = ["Acceptance Criteria", "Acceptance criteria", "acceptance criteria"]
_AC_KEYWORDS = {"must", "should", "returns", "produces", "passes", "fails",
                "given", "when", "then", "assert", "verify", "expect"}
_MIN_AC_KEYWORDS = 2
_ITEM_RE_PREFIXES = ("-", "*", "+")


def _has_classification(text: str) -> bool:
    text_lower = text.lower()
    return ("afk" in text_lower or "hitl" in text_lower or
            "autonomous" in text_lower or "human-in-the-loop" in text_lower)


def _ac_section_body(text: str) -> str:
    """Return the body of the Acceptance Criteria section."""
    for alias in _AC_ALIASES:
        body = extract_section(text, alias)
        if body.strip():
            return body
    return ""


def _count_list_items(text: str) -> int:
    """Count bullet/numbered list items in text."""
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if s and (s[0] in _ITEM_RE_PREFIXES or (len(s) > 2 and s[0].isdigit() and s[1] in ".)")):
            count += 1
    return count


def _ac_keyword_density(ac_body: str) -> float:
    """Fraction of AC keywords present in the AC section (0.0–1.0).

    Scoping to the AC section avoids crediting keyword occurrences elsewhere
    in the document (e.g. Requirements) as evidence of testable criteria.
    """
    if not ac_body.strip():
        return 0.0
    lower = ac_body.lower()
    hits = sum(1 for kw in _AC_KEYWORDS if kw in lower)
    return min(hits / _MIN_AC_KEYWORDS, 1.0)


def _ac_item_score(ac_body: str, expected: int = 3) -> float:
    """Normalize item count against expected minimum (capped at 1.0)."""
    n = _count_list_items(ac_body)
    return min(n / expected, 1.0) if expected > 0 else 0.0


class PlanEvaluator(Evaluator):
    name = "plan_evaluator"

    def evaluate(self, result: TaskResult, task: Task) -> TaskResult:
        if result.error:
            result.accuracy = 0.0
            result.quality_score = 0.0
            return result

        merged_text, source = _merge_content(
            result.raw_output, result.workspace_snapshot,
        )

        if not merged_text.strip():
            result.accuracy = 0.0
            result.quality_score = 0.0
            result.evaluator_details = {"content_source": source}
            return result

        required = task.gold_standard.required_sections or _REQUIRED_SECTIONS
        tp, fp, fn = _score_completeness(merged_text, required)

        all_present = fn == 0
        result.accuracy = 1.0 if all_present else tp / len(required)

        ac_body = _ac_section_body(merged_text)
        has_classify = _has_classification(merged_text)
        ac_density = _ac_keyword_density(ac_body)
        ac_items = _count_list_items(ac_body)
        ac_item_score = _ac_item_score(ac_body)

        completeness_score = result.accuracy
        classify_score = 1.0 if has_classify else 0.0

        result.quality_score = 10.0 * (
            _QUALITY_WEIGHTS["completeness"] * completeness_score
            + _QUALITY_WEIGHTS["acceptance_criteria_density"] * ac_density
            + _QUALITY_WEIGHTS["classification_present"] * classify_score
            + _QUALITY_WEIGHTS["criteria_item_count"] * ac_item_score
        )

        result.evaluator_details = {
            "content_source": source,
            "sections_found": tp,
            "sections_missing": fn,
            "sections_extra": fp,
            "has_classification": has_classify,
            "ac_keyword_density": round(ac_density, 2),
            "ac_item_count": ac_items,
        }
        return result
