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
    uv run scripts/render_task.py --input task.json --output tasks/issues/001-example.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from jinja2 import Template

JsonObject = dict[str, object]
_TASK_PATH = re.compile(r"^tasks/issues/\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ISSUE_ID = re.compile(r"^\d{3}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{[^}]+\}\}")
_TEMPLATE_PATH = Path(__file__).with_name("task_template.md.j2")


class TaskRule(Protocol):
    def check(self, task: JsonObject) -> None:
        """Validate one task concern.

        Example:
            ScalarRule("id", _ISSUE_ID, "three digits").check({"id": "001"})
        """


@dataclass(frozen=True)
class RequirementGroup:
    field: str
    prefix: str


@dataclass(frozen=True)
class TestCategory:
    field: str
    heading: str
    prefix: str


@dataclass(frozen=True)
class ScalarRule:
    field: str
    pattern: re.Pattern[str]
    expected: str

    def check(self, task: JsonObject) -> None:
        value = task.get(self.field)
        if isinstance(value, str) and self.pattern.match(value):
            return
        raise ScriptError(f"invalid {self.field} {value!r}; expected {self.expected}")


@dataclass(frozen=True)
class TextRule:
    field: str

    def check(self, task: JsonObject) -> None:
        value = task.get(self.field)
        validate_text(self.field, value)


@dataclass(frozen=True)
class TextListRule:
    field: str

    def check(self, task: JsonObject) -> None:
        value = task.get(self.field)
        validate_text_list(self.field, value)


@dataclass(frozen=True)
class ItemListRule:
    field: str
    prefix: str

    def check(self, task: JsonObject) -> None:
        validate_item_list(self.field, task.get(self.field), self.prefix)


class AssignabilityRule:
    def check(self, task: JsonObject) -> None:
        value = task.get("assignability")
        if not isinstance(value, dict):
            raise ScriptError(f"invalid assignability {value!r}; expected object")
        mode = value.get("mode")
        reason = value.get("reason")
        if mode in {"AFK", "HITL"} and isinstance(reason, str) and reason.strip():
            reject_placeholder("assignability.reason", reason)
            return
        raise ScriptError(f"invalid assignability {value!r}; expected AFK/HITL reason")


class RequiredTestsRule:
    def __init__(self, categories: Sequence[TestCategory]) -> None:
        self._categories = categories

    def check(self, task: JsonObject) -> None:
        raw_tests = task.get("required_tests")
        if not isinstance(raw_tests, dict):
            raise ScriptError(f"invalid required_tests {raw_tests!r}; expected object")
        task["required_tests"] = [
            self._normalize_category(raw_tests, category)
            for category in self._categories
        ]

    def _normalize_category(
        self, raw_tests: JsonObject, category: TestCategory
    ) -> JsonObject:
        entries = validate_test_entries(
            category.field, raw_tests.get(category.field), category.prefix
        )
        return {"heading": category.heading, "entries": entries}


class ScriptError(RuntimeError):
    pass


class TaskLoader:
    def load(self, path: Path) -> JsonObject:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ScriptError(f"invalid JSON in {path}: {exc}") from exc
        if isinstance(payload, dict):
            return payload
        raise ScriptError(
            f"invalid task input {type(payload).__name__}; expected object"
        )


class TaskNormalizer:
    def normalize(self, payload: JsonObject) -> JsonObject:
        today = datetime.now(UTC).date().isoformat()
        task = dict(payload)
        task.setdefault("created", today)
        task.setdefault("updated", task["created"])
        return task


class TaskValidator:
    def __init__(self, rules: Sequence[TaskRule]) -> None:
        self._rules = rules

    def validate(self, task: JsonObject) -> None:
        for rule in self._rules:
            rule.check(task)


class TaskRenderer:
    def render(self, task: JsonObject) -> str:
        rendered = str(
            Template(_TEMPLATE_PATH.read_text(encoding="utf-8")).render(task=task)
        )
        return rendered.rstrip() + "\n"


class TaskWriter:
    def write(self, path: Path, content: str) -> None:
        self.validate_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def validate_path(self, path: Path) -> None:
        normalized = path.as_posix()
        if _TASK_PATH.match(normalized):
            return
        raise ScriptError(
            f"invalid output path {normalized!r}; expected tasks/issues/NNN-kebab-slug.md"
        )


class TaskRenderFacade:
    def __init__(self, validator: TaskValidator) -> None:
        self._loader = TaskLoader()
        self._normalizer = TaskNormalizer()
        self._validator = validator
        self._renderer = TaskRenderer()
        self._writer = TaskWriter()

    def render_file(self, input_path: Path, output_path: Path) -> None:
        task = self._normalizer.normalize(self._loader.load(input_path))
        self._validator.validate(task)
        self._writer.write(output_path, self._renderer.render(task))


def main() -> None:
    try:
        args = _parse_args()
        TaskRenderFacade(default_validator()).render_file(args.input, args.output)
    except ScriptError as exc:
        raise SystemExit(str(exc)) from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a plan-it task file")
    parser.add_argument("--input", required=True, type=Path, help="Task JSON input")
    parser.add_argument("--output", required=True, type=Path, help="Task Markdown path")
    return parser.parse_args()


def default_validator() -> TaskValidator:
    rules: list[TaskRule] = [
        ScalarRule("id", _ISSUE_ID, "three digits such as 001"),
        ScalarRule("created", _DATE, "YYYY-MM-DD"),
        ScalarRule("updated", _DATE, "YYYY-MM-DD"),
        TextRule("title"),
        TextRule("priority"),
        AssignabilityRule(),
        *[TextListRule(field) for field in text_list_fields()],
        *[ItemListRule(group.field, group.prefix) for group in requirement_groups()],
        ItemListRule("acceptance_criteria", "AC"),
        RequiredTestsRule(test_categories()),
    ]
    return TaskValidator(rules)


def text_list_fields() -> tuple[str, ...]:
    return (
        "dependencies",
        "context",
        "use_cases",
        "definition_of_ready",
        "definition_of_done",
    )


def requirement_groups() -> tuple[RequirementGroup, ...]:
    return (
        RequirementGroup("functional_requirements", "FR"),
        RequirementGroup("non_functional_requirements", "NFR"),
        RequirementGroup("observability_requirements", "OBS"),
    )


def test_categories() -> tuple[TestCategory, ...]:
    return (
        TestCategory("unit_tests", "Unit Tests", "UT"),
        TestCategory("integration_tests", "Integration Tests", "IT"),
        TestCategory("smoke_tests", "Smoke Tests", "SMK"),
        TestCategory("end_to_end_tests", "End-to-End Tests", "E2E"),
        TestCategory("regression_tests", "Regression Tests", "REG"),
        TestCategory("performance_tests", "Performance Tests", "PT"),
        TestCategory("security_tests", "Security Tests", "ST"),
        TestCategory("usability_tests", "Usability Tests", "UX"),
        TestCategory("observability_tests", "Observability Tests", "OT"),
    )


def validate_text(label: str, value: object) -> str:
    if isinstance(value, str) and value.strip():
        reject_placeholder(label, value)
        return value
    raise ScriptError(f"invalid {label} {value!r}; expected non-empty string")


def validate_text_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ScriptError(f"invalid {label} {value!r}; expected non-empty string list")
    return [
        validate_text(f"{label}[{index}]", item) for index, item in enumerate(value)
    ]


def validate_item_list(label: str, value: object, prefix: str) -> None:
    if not isinstance(value, list) or not value:
        raise ScriptError(f"invalid {label} {value!r}; expected non-empty item list")
    for index, item in enumerate(value):
        validate_item(label, index, item, prefix)


def validate_item(label: str, index: int, item: object, prefix: str) -> None:
    if not isinstance(item, dict):
        raise ScriptError(f"invalid {label}[{index}] {item!r}; expected object")
    expected_id = f"{prefix}-{index + 1:03d}"
    if item.get("id") != expected_id:
        raise ScriptError(
            f"invalid {label}[{index}].id {item.get('id')!r}; expected {expected_id}"
        )
    validate_text(f"{label}[{index}].text", item.get("text"))


def validate_test_entries(label: str, value: object, prefix: str) -> list[JsonObject]:
    if not isinstance(value, list) or not value:
        raise ScriptError(
            f"invalid required_tests.{label} {value!r}; expected non-empty list"
        )
    return [
        validate_test_entry(label, index, item, prefix)
        for index, item in enumerate(value)
    ]


def validate_test_entry(
    label: str, index: int, item: object, prefix: str
) -> JsonObject:
    if not isinstance(item, dict):
        raise ScriptError(
            f"invalid required_tests.{label}[{index}] {item!r}; expected object"
        )
    expected_id = f"{prefix}-{index + 1:03d}"
    if item.get("id") != expected_id:
        raise ScriptError(
            f"invalid required_tests.{label}[{index}].id {item.get('id')!r}; expected {expected_id}"
        )
    text = validate_text(f"required_tests.{label}[{index}].text", item.get("text"))
    covers = item.get("covers", "")
    if not isinstance(covers, str):
        raise ScriptError(
            f"invalid required_tests.{label}[{index}].covers {covers!r}; expected string"
        )
    reject_placeholder(f"required_tests.{label}[{index}].covers", covers)
    return {"id": expected_id, "text": text, "covers": covers}


def reject_placeholder(label: str, value: str) -> None:
    match = _PLACEHOLDER.search(value)
    if match:
        raise ScriptError(
            f"invalid {label} {value!r}; unresolved placeholder {match.group(0)!r}"
        )


if __name__ == "__main__":
    main()
