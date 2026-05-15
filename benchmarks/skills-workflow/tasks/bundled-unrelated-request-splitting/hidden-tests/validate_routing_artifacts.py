from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def flatten_strings(value: Any) -> str:
    parts: list[str] = []
    if isinstance(value, str):
        parts.append(value)
    elif isinstance(value, list):
        for item in value:
            parts.append(flatten_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            parts.append(flatten_strings(item))
    return " ".join(part for part in parts if part)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def has_any(text: str, patterns: list[str]) -> bool:
    lowered = normalize_text(text)
    return any(pattern.lower() in lowered for pattern in patterns)


def count_topics(text: str, topics: list[dict[str, Any]]) -> tuple[int, list[str]]:
    matched = [topic["id"] for topic in topics if has_any(text, topic["any"])]
    return len(matched), matched


def find_matching_entries(entries: list[str], patterns: list[str]) -> list[str]:
    return [entry for entry in entries if has_any(entry, patterns)]


def count_reason_concept_matches(text: str, concept_groups: list[list[str]]) -> int:
    return sum(1 for group in concept_groups if has_any(text, group))


def has_topic_specific_reason(entry: str, topic: dict[str, Any]) -> bool:
    if has_any(entry, topic.get("reason_any", [])):
        return True

    concept_groups = topic.get("reason_concept_groups_any", [])
    min_groups = topic.get("reason_min_concept_groups", 0)
    return bool(concept_groups) and count_reason_concept_matches(entry, concept_groups) >= min_groups


def sentence_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]|$)", text):
        sentence = match.group(0).strip()
        if sentence:
            spans.append((match.start(), match.end(), sentence))
    return spans


def classify_forbidden_phrase_usage(
    text: str,
    phrases: list[str],
    approval_signals: list[str],
    rejection_signals: list[str],
) -> list[str]:
    normalized = normalize_text(text)
    spans = sentence_spans(normalized)
    problems: list[str] = []

    for phrase in phrases:
        start = 0
        needle = phrase.lower()
        while True:
            index = normalized.find(needle, start)
            if index == -1:
                break

            sentence = next(
                (snippet for span_start, span_end, snippet in spans if span_start <= index < span_end),
                normalized[max(0, index - 100): index + len(needle) + 100].strip(),
            )
            has_rejection_signal = any(signal.lower() in sentence for signal in rejection_signals)
            has_approval_signal = any(signal.lower() in sentence for signal in approval_signals)

            if has_approval_signal and not has_rejection_signal:
                problems.append(f"'{phrase}' in approving context: {sentence}")

            start = index + len(needle)

    return problems


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_max_len(value: str, max_len: int, label: str, errors: list[str]) -> None:
    require(len(value) <= max_len, f"{label} must be <= {max_len} chars; found {len(value)}", errors)


def require_exact_count(entries: list[Any], expected: int, label: str, errors: list[str]) -> None:
    require(len(entries) == expected, f"{label} must contain exactly {expected} entries; found {len(entries)}", errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    args = parser.parse_args()

    rules = read_json(args.rules)
    issue = read_json(args.artifacts_dir / "issue-split.json")
    validation = read_json(args.artifacts_dir / "validation-report.json")
    topics = rules["request_topics"]
    routing_signals = rules["routing_signals"]
    forbidden_single_route = rules["forbidden_single_route_signals"]
    approval_context_signals = rules.get("approval_context_signals", [])
    rejection_context_signals = rules.get("rejection_context_signals", [])
    efficiency = rules.get("efficiency", {})

    errors: list[str] = []

    issue_text = flatten_strings(issue)
    issue_scope_entries = issue.get("scope", [])
    issue_scope_text = flatten_strings(issue_scope_entries)
    issue_non_goals_entries = issue.get("non_goals", [])
    issue_non_goals_text = flatten_strings(issue_non_goals_entries)
    issue_acceptance_entries = issue.get("acceptance_criteria", [])
    issue_acceptance_text = flatten_strings(issue_acceptance_entries)
    issue_validation_entries = issue.get("validation_expectations", [])
    issue_topic_count, issue_topics = count_topics(issue_text, topics)

    require_exact_count(issue_scope_entries, efficiency["issue_scope_exact_count"], "issue-split.json scope", errors)
    require_exact_count(issue_acceptance_entries, efficiency["issue_acceptance_exact_count"], "issue-split.json acceptance_criteria", errors)
    require_exact_count(issue_non_goals_entries, efficiency["issue_non_goals_exact_count"], "issue-split.json non_goals", errors)
    require_exact_count(issue_validation_entries, efficiency["issue_validation_expectations_exact_count"], "issue-split.json validation_expectations", errors)
    require_max_len(issue.get("summary", ""), efficiency["max_summary_chars"], "issue-split.json summary", errors)
    require_max_len(issue.get("problem", ""), efficiency["max_problem_chars"], "issue-split.json problem", errors)
    for entry in issue_scope_entries:
        require_max_len(entry, efficiency["max_scope_entry_chars"], "issue-split.json scope entry", errors)
    for entry in issue_acceptance_entries:
        require_max_len(entry, efficiency["max_acceptance_entry_chars"], "issue-split.json acceptance_criteria entry", errors)
    for entry in issue_non_goals_entries:
        require_max_len(entry, efficiency["max_non_goal_entry_chars"], "issue-split.json non_goals entry", errors)
    for entry in issue_validation_entries:
        require_max_len(entry, efficiency["max_validation_entry_chars"], "issue-split.json validation_expectations entry", errors)
    non_goal_topic_count, non_goal_topics = count_topics(issue_non_goals_text, topics)

    require(issue_topic_count == len(topics), f"issue-split.json must reference all bundled requests; found {issue_topics}", errors)
    require(non_goal_topic_count == len(topics), f"issue-split.json non_goals must explicitly exclude all bundled requests; found {non_goal_topics}", errors)
    require(has_any(issue_scope_text, routing_signals), "issue-split.json scope must describe splitting/rejection/routing rather than implementation", errors)
    require(has_any(issue_acceptance_text, routing_signals), "issue-split.json acceptance_criteria must confirm bundled execution is split or rejected", errors)

    for topic in topics:
        scope_entries = find_matching_entries(issue_scope_entries, topic["any"])
        acceptance_entries = find_matching_entries(issue_acceptance_entries, topic["any"])
        validation_entries = find_matching_entries(issue_validation_entries, topic["any"])

        require(scope_entries, f"issue-split.json scope must include a dedicated slice entry for {topic['id']}", errors)
        require(acceptance_entries, f"issue-split.json acceptance_criteria must include a dedicated follow-up condition for {topic['id']}", errors)
        require(validation_entries, f"issue-split.json validation_expectations must include a dedicated routing note for {topic['id']}", errors)
        require(
            any(has_any(entry, topic["work_type_any"]) for entry in scope_entries),
            f"issue-split.json scope entry for {topic['id']} must classify the slice by surface or work type",
            errors,
        )
        require(
            any(has_any(entry, topic["route_any"]) for entry in validation_entries),
            f"issue-split.json validation_expectations for {topic['id']} must include a downstream route hint",
            errors,
        )
    issue_forbidden_usage = classify_forbidden_phrase_usage(
        issue_text,
        forbidden_single_route,
        approval_context_signals,
        rejection_context_signals,
    )
    require(
        not issue_forbidden_usage,
        "issue-split.json must not approve a single combined implementation route"
        + (f"; found {issue_forbidden_usage[0]}" if issue_forbidden_usage else ""),
        errors,
    )

    validation_text = flatten_strings(validation)
    validation_findings_entries = validation.get("findings", [])
    validation_findings_text = flatten_strings(validation_findings_entries)
    validation_recommendation_text = flatten_strings(validation.get("recommendation", ""))
    validation_topic_count, validation_topics = count_topics(validation_text, topics)

    require_exact_count(validation.get("checks_run", []), efficiency["checks_run_exact_count"], "validation-report.json checks_run", errors)
    require_exact_count(validation_findings_entries, efficiency["validation_findings_exact_count"], "validation-report.json findings", errors)
    for entry in validation_findings_entries:
        require_max_len(entry, efficiency["max_finding_entry_chars"], "validation-report.json finding entry", errors)
    require_max_len(validation.get("recommendation", ""), efficiency["max_recommendation_chars"], "validation-report.json recommendation", errors)

    require(
        validation.get("status") in rules["validation"]["allowed_statuses"],
        f"validation-report.json status must be one of {rules['validation']['allowed_statuses']}",
        errors,
    )
    require(
        validation_topic_count >= rules["validation"]["min_topics_mentioned"],
        f"validation-report.json must mention the bundled request areas; found {validation_topics}",
        errors,
    )
    require(has_any(validation_findings_text, routing_signals), "validation-report.json findings must explain that the request should be split/rejected", errors)
    require(has_any(validation_recommendation_text, routing_signals), "validation-report.json recommendation must route the work into separate follow-up issues", errors)
    total_chars = len(issue_text) + len(validation_text)
    require(total_chars <= efficiency["max_total_chars"], f"combined artifact text must be <= {efficiency['max_total_chars']} chars; found {total_chars}", errors)

    for topic in topics:
        matching_findings = find_matching_entries(validation_findings_entries, topic["any"])
        require(matching_findings, f"validation-report.json findings must include a distinct reason for splitting {topic['id']}", errors)
        require(
            any(has_topic_specific_reason(entry, topic) for entry in matching_findings),
            f"validation-report.json findings for {topic['id']} must explain the slice-specific reason it should be split",
            errors,
        )
        require(
            has_any(validation_recommendation_text, topic["any"]),
            f"validation-report.json recommendation must mention the follow-up route for {topic['id']}",
            errors,
        )
    validation_forbidden_usage = classify_forbidden_phrase_usage(
        validation_text,
        forbidden_single_route,
        approval_context_signals,
        rejection_context_signals,
    )
    require(
        not validation_forbidden_usage,
        "validation-report.json must not approve a single combined implementation route"
        + (f"; found {validation_forbidden_usage[0]}" if validation_forbidden_usage else ""),
        errors,
    )

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"Routing artifact checks passed. total_chars={total_chars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
