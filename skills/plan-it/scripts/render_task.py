#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "jinja2==3.1.6",
# ]
# [tool.uv]
# exclude-newer = "2026-05-30T00:00:00Z"
# ///
"""Render a validated plan-it task file from JSON.

Usage:
    uv run skills/plan-it/scripts/render_task.py --input task.json --output tasks/issues/001-example.md
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Template

_TASK_PATH = re.compile(r"^tasks/issues/\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ISSUE_ID = re.compile(r"^\d{3}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{[^}]+\}\}")
_REQUIREMENT_PREFIXES = {
    "functional_requirements": "FR",
    "non_functional_requirements": "NFR",
    "observability_requirements": "OBS",
}
_TEST_CATEGORIES = {
    "unit_tests": ("Unit Tests", "UT"),
    "integration_tests": ("Integration Tests", "IT"),
    "smoke_tests": ("Smoke Tests", "SMK"),
    "end_to_end_tests": ("End-to-End Tests", "E2E"),
    "regression_tests": ("Regression Tests", "REG"),
    "performance_tests": ("Performance Tests", "PT"),
    "security_tests": ("Security Tests", "ST"),
    "usability_tests": ("Usability Tests", "UX"),
    "observability_tests": ("Observability Tests", "OT"),
}

_TEMPLATE = Template(
    """---
id: "{{ task.id }}"
created: {{ task.created }}
updated: {{ task.updated }}
status: active
---

# Task: {{ task.title }}

## Priority

{{ task.priority }}

## Dependencies

{% for dependency in task.dependencies -%}
- {{ dependency }}
{% endfor %}
## Assignability

**{{ task.assignability.mode }}** — {{ task.assignability.reason }}

## Context

{% for item in task.context -%}
{{ item }}

{% endfor -%}
## Use Cases

{% for item in task.use_cases -%}
- {{ item }}
{% endfor %}
## Definition of Ready

{% for item in task.definition_of_ready -%}
- {{ item }}
{% endfor %}
## Functional Requirements

{% for requirement in task.functional_requirements -%}
- `{{ requirement.id }}`: {{ requirement.text }}
{% endfor %}
## Non-Functional Requirements

{% for requirement in task.non_functional_requirements -%}
- `{{ requirement.id }}`: {{ requirement.text }}
{% endfor %}
## Observability Requirements

{% for requirement in task.observability_requirements -%}
- `{{ requirement.id }}`: {{ requirement.text }}
{% endfor %}
## Acceptance Criteria

{% for criterion in task.acceptance_criteria -%}
- `{{ criterion.id }}`: {{ criterion.text }}
{% endfor %}
## Required Tests

{% for category in task.required_tests -%}
### {{ category.heading }}

{% for test in category.entries -%}
- `{{ test.id }}`: {{ test.text }}{% if test.covers %} Covers {{ test.covers }}.{% endif %}
{% endfor %}
{% endfor -%}
## Definition of Done

{% for item in task.definition_of_done -%}
- {{ item }}
{% endfor -%}
"""
)


def main() -> None:
    args = _parse_args()
    task = _load_task(args.input)
    _validate_output_path(args.output)
    rendered = _render(task)
    _write_output(args.output, rendered)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a plan-it task file")
    parser.add_argument("--input", required=True, type=Path, help="Task JSON input")
    parser.add_argument("--output", required=True, type=Path, help="Task Markdown path")
    return parser.parse_args()


def _load_task(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(
            f"invalid task input {type(payload).__name__}; expected object"
        )
    return _normalize_task(payload)


def _normalize_task(payload: dict[str, object]) -> dict[str, object]:
    today = datetime.now(UTC).date().isoformat()
    task = dict(payload)
    task.setdefault("created", today)
    task.setdefault("updated", task["created"])
    _validate_task(task)
    task["required_tests"] = _normalize_tests(task["required_tests"])
    return task


def _validate_task(task: dict[str, object]) -> None:
    _validate_scalar(task, "id", _ISSUE_ID, "three digits such as 001")
    _validate_scalar(task, "created", _DATE, "YYYY-MM-DD")
    _validate_scalar(task, "updated", _DATE, "YYYY-MM-DD")
    for key in ("title", "priority"):
        _validate_text(task, key)
    _validate_assignability(task.get("assignability"))
    for key in _list_sections():
        _validate_text_list(task, key)
    for key, prefix in _REQUIREMENT_PREFIXES.items():
        _validate_items(task, key, prefix)
    _validate_items(task, "acceptance_criteria", "AC")


def _list_sections() -> tuple[str, ...]:
    return (
        "dependencies",
        "context",
        "use_cases",
        "definition_of_ready",
        "definition_of_done",
    )


def _validate_scalar(
    task: dict[str, object], key: str, pattern: re.Pattern[str], expected: str
) -> None:
    value = task.get(key)
    if not isinstance(value, str) or not pattern.match(value):
        raise SystemExit(f"invalid {key} {value!r}; expected {expected}")


def _validate_text(task: dict[str, object], key: str) -> None:
    value = task.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"invalid {key} {value!r}; expected non-empty string")
    _reject_placeholder(key, value)


def _validate_text_list(task: dict[str, object], key: str) -> None:
    value = task.get(key)
    if not isinstance(value, list) or not value:
        raise SystemExit(f"invalid {key} {value!r}; expected non-empty string list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(
                f"invalid {key}[{index}] {item!r}; expected non-empty string"
            )
        _reject_placeholder(f"{key}[{index}]", item)


def _validate_assignability(value: object) -> None:
    if not isinstance(value, dict):
        raise SystemExit(f"invalid assignability {value!r}; expected object")
    mode = value.get("mode")
    reason = value.get("reason")
    if mode not in {"AFK", "HITL"} or not isinstance(reason, str) or not reason.strip():
        raise SystemExit(
            f"invalid assignability {value!r}; expected mode AFK/HITL and reason"
        )
    _reject_placeholder("assignability.reason", reason)


def _validate_items(task: dict[str, object], key: str, prefix: str) -> None:
    value = task.get(key)
    if not isinstance(value, list) or not value:
        raise SystemExit(f"invalid {key} {value!r}; expected non-empty item list")
    for index, item in enumerate(value):
        _validate_item(key, index, item, prefix)


def _validate_item(key: str, index: int, item: object, prefix: str) -> None:
    if not isinstance(item, dict):
        raise SystemExit(f"invalid {key}[{index}] {item!r}; expected object")
    expected_id = f"{prefix}-{index + 1:03d}"
    if item.get("id") != expected_id:
        raise SystemExit(
            f"invalid {key}[{index}].id {item.get('id')!r}; expected {expected_id}"
        )
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        raise SystemExit(
            f"invalid {key}[{index}].text {text!r}; expected non-empty string"
        )
    _reject_placeholder(f"{key}[{index}].text", text)


def _normalize_tests(raw_tests: object) -> list[dict[str, object]]:
    if not isinstance(raw_tests, dict):
        raise SystemExit(f"invalid required_tests {raw_tests!r}; expected object")
    return [
        {"heading": heading, "entries": _test_entries(raw_tests, key, prefix)}
        for key, (heading, prefix) in _TEST_CATEGORIES.items()
    ]


def _test_entries(
    raw_tests: dict[str, object], key: str, prefix: str
) -> list[dict[str, str]]:
    value = raw_tests.get(key)
    if not isinstance(value, list) or not value:
        raise SystemExit(
            f"invalid required_tests.{key} {value!r}; expected non-empty list"
        )
    entries = []
    for index, item in enumerate(value):
        entries.append(_normalize_test_entry(key, index, item, prefix))
    return entries


def _normalize_test_entry(
    key: str, index: int, item: object, prefix: str
) -> dict[str, str]:
    if not isinstance(item, dict):
        raise SystemExit(
            f"invalid required_tests.{key}[{index}] {item!r}; expected object"
        )
    expected_id = f"{prefix}-{index + 1:03d}"
    if item.get("id") != expected_id:
        raise SystemExit(
            f"invalid required_tests.{key}[{index}].id {item.get('id')!r}; expected {expected_id}"
        )
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        raise SystemExit(
            f"invalid required_tests.{key}[{index}].text {text!r}; expected non-empty string"
        )
    covers = item.get("covers", "")
    if not isinstance(covers, str):
        raise SystemExit(
            f"invalid required_tests.{key}[{index}].covers {covers!r}; expected string"
        )
    _reject_placeholder(f"required_tests.{key}[{index}]", text + covers)
    return {"id": expected_id, "text": text, "covers": covers}


def _reject_placeholder(label: str, value: str) -> None:
    match = _PLACEHOLDER.search(value)
    if match:
        raise SystemExit(
            f"invalid {label} {value!r}; unresolved placeholder {match.group(0)!r}"
        )


def _validate_output_path(path: Path) -> None:
    normalized = path.as_posix()
    if not _TASK_PATH.match(normalized):
        raise SystemExit(
            f"invalid output path {normalized!r}; expected tasks/issues/NNN-kebab-slug.md"
        )


def _render(task: dict[str, object]) -> str:
    rendered = str(_TEMPLATE.render(task=task))
    return rendered.rstrip() + "\n"


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
