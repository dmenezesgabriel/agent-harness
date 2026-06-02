#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "jinja2==3.1.6",
# ]
# [tool.uv]
# exclude-newer = "2026-05-30T00:00:00Z"
# ///
"""Render a validated implement-it summary file from JSON.

Usage:
    uv run scripts/render_implementation.py --input summary.json --output tasks/implementation/003-age-validator-summary.md
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
_SUMMARY_PATH = re.compile(
    r"^tasks/implementation/\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*-summary\.md$"
)
_SUMMARY_ID = re.compile(r"^\d{3}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{[^}]+\}\}")
_TEMPLATE_PATH = Path(__file__).with_name("implementation_template.md.j2")


class SummaryRule(Protocol):
    def check(self, summary: JsonObject) -> None:
        ...


@dataclass(frozen=True)
class ScalarRule:
    field: str
    pattern: re.Pattern[str]
    expected: str

    def check(self, summary: JsonObject) -> None:
        value = summary.get(self.field)
        if isinstance(value, str) and self.pattern.match(value):
            return
        raise ScriptError(
            f"invalid {self.field} {value!r}; expected {self.expected}"
        )


@dataclass(frozen=True)
class TextRule:
    field: str

    def check(self, summary: JsonObject) -> None:
        value = summary.get(self.field)
        if isinstance(value, str) and value.strip():
            reject_placeholder(self.field, value)
            return
        raise ScriptError(f"invalid {self.field} {value!r}; expected non-empty string")


@dataclass(frozen=True)
class TextListRule:
    field: str

    def check(self, summary: JsonObject) -> None:
        value = summary.get(self.field)
        validate_text_list(self.field, value)


@dataclass(frozen=True)
class ItemListRule:
    field: str
    sub_fields: tuple[str, ...]

    def check(self, summary: JsonObject) -> None:
        value = summary.get(self.field)
        validate_item_list(self.field, value, self.sub_fields)


class ScriptError(RuntimeError):
    pass


class SummaryLoader:
    def load(self, path: Path) -> JsonObject:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ScriptError(f"invalid JSON in {path}: {exc}") from exc
        if isinstance(payload, dict):
            return payload
        raise ScriptError(
            f"invalid summary input {type(payload).__name__}; expected object"
        )


class SummaryNormalizer:
    def normalize(self, payload: JsonObject) -> JsonObject:
        today = datetime.now(UTC).date().isoformat()
        summary = dict(payload)
        summary.setdefault("created", today)
        summary.setdefault("updated", summary["created"])
        return summary


class SummaryValidator:
    def __init__(self, rules: Sequence[SummaryRule]) -> None:
        self._rules = rules

    def validate(self, summary: JsonObject) -> None:
        for rule in self._rules:
            rule.check(summary)


class SummaryRenderer:
    def render(self, summary: JsonObject) -> str:
        rendered = str(
            Template(_TEMPLATE_PATH.read_text(encoding="utf-8")).render(
                summary=summary
            )
        )
        return rendered.rstrip() + "\n"


class SummaryWriter:
    def write(self, path: Path, content: str) -> None:
        self.validate_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def validate_path(self, path: Path) -> None:
        normalized = path.as_posix()
        if _SUMMARY_PATH.match(normalized):
            return
        raise ScriptError(
            f"invalid output path {normalized!r}; expected tasks/implementation/NNN-kebab-slug-summary.md"
        )


class SummaryRenderFacade:
    def __init__(self, validator: SummaryValidator) -> None:
        self._loader = SummaryLoader()
        self._normalizer = SummaryNormalizer()
        self._validator = validator
        self._renderer = SummaryRenderer()
        self._writer = SummaryWriter()

    def render_file(self, input_path: Path, output_path: Path) -> None:
        summary = self._normalizer.normalize(self._loader.load(input_path))
        self._validator.validate(summary)
        self._writer.write(output_path, self._renderer.render(summary))


def main() -> None:
    try:
        args = _parse_args()
        SummaryRenderFacade(default_validator()).render_file(
            args.input, args.output
        )
    except ScriptError as exc:
        raise SystemExit(str(exc)) from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an implement-it summary file"
    )
    parser.add_argument("--input", required=True, type=Path, help="Summary JSON input")
    parser.add_argument(
        "--output", required=True, type=Path, help="Summary Markdown path"
    )
    return parser.parse_args()


def default_validator() -> SummaryValidator:
    rules: list[SummaryRule] = [
        ScalarRule("id", _SUMMARY_ID, "three digits such as 003"),
        ScalarRule("created", _DATE, "YYYY-MM-DD"),
        ScalarRule("updated", _DATE, "YYYY-MM-DD"),
        TextRule("issue"),
        TextRule("title"),
        TextRule("related_task"),
        *[TextListRule(field) for field in text_list_fields()],
        *[ItemListRule(field, sub_fields) for field, sub_fields in item_list_fields()],
    ]
    return SummaryValidator(rules)


def text_list_fields() -> tuple[str, ...]:
    return ("test_categories_na",)


def item_list_fields() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return (
        ("files_changed", ("path", "reason")),
    )


def validate_text_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ScriptError(
            f"invalid {label} {value!r}; expected non-empty string list"
        )
    return [
        validate_text(f"{label}[{index}]", item)
        for index, item in enumerate(value)
    ]


def validate_text(label: str, value: object) -> str:
    if isinstance(value, str) and value.strip():
        reject_placeholder(label, value)
        return value
    raise ScriptError(f"invalid {label} {value!r}; expected non-empty string")


def validate_item_list(
    label: str, value: object, sub_fields: tuple[str, ...]
) -> None:
    if not isinstance(value, list) or not value:
        raise ScriptError(
            f"invalid {label} {value!r}; expected non-empty item list"
        )
    for index, item in enumerate(value):
        validate_item(label, index, item, sub_fields)


def validate_item(
    label: str, index: int, item: object, sub_fields: tuple[str, ...]
) -> None:
    if not isinstance(item, dict):
        raise ScriptError(
            f"invalid {label}[{index}] {item!r}; expected object"
        )
    for field in sub_fields:
        validate_text(f"{label}[{index}].{field}", item.get(field))


def reject_placeholder(label: str, value: str) -> None:
    match = _PLACEHOLDER.search(value)
    if match:
        raise ScriptError(
            f"invalid {label} {value!r}; unresolved placeholder {match.group(0)!r}"
        )


if __name__ == "__main__":
    main()
