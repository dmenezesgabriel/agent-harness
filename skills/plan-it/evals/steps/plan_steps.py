"""Behave step definitions for plan-it generated task validation."""

import re
from typing import Protocol

from behave import given, then  # type: ignore[import-untyped]

_ISSUE_LOCATION = re.compile(r"^tasks/issues/.+\.md$")
_ISSUE_PATH = re.compile(r"^tasks/issues/\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ADR_PATH = re.compile(r"^docs/adrs/\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_FRONTMATTER_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
_FRONTMATTER_FIELD = re.compile(r"^(\w+):\s*(.+?)\s*$", re.MULTILINE)
_DATE_VALUE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{[^}]+\}\}")
_REQUIREMENT_ID = re.compile(r"`(?:FR|NFR|OBS)-\d{3}`")
_ACCEPTANCE_ID = re.compile(r"`AC-\d{3}`")
_TEST_ID = re.compile(r"`(?:UT|IT|SMK|E2E|REG|PT|ST|UX|OT)-\d{3}`")
_ASSIGNABILITY = re.compile(r"\*\*(?:AFK|HITL)\*\*\s+—\s+\S+", re.MULTILINE)
_VAGUE_DEPENDENCY = re.compile(
    r"^-\s*(?:Depends on backend|Depends on frontend|Depends on architecture|"
    r"Depends on other tasks|Needs some setup)\.?$",
    re.IGNORECASE | re.MULTILINE,
)
_NOT_APPLICABLE = re.compile(r"Not applicable\s+—\s+([^.\n]+)", re.IGNORECASE)

_REQUIRED_FRONTMATTER_FIELDS = {"id", "created", "updated", "status"}
_REQUIRED_SECTIONS = [
    "## Priority",
    "## Dependencies",
    "## Assignability",
    "## Context",
    "## Use Cases",
    "## Definition of Ready",
    "## Functional Requirements",
    "## Non-Functional Requirements",
    "## Observability Requirements",
    "## Acceptance Criteria",
    "## Required Tests",
    "## Definition of Done",
]
_GENERIC_NOT_APPLICABLE_REASONS = {"n/a", "none", "not needed", "not relevant"}


class PlanContext(Protocol):
    artifacts: dict[str, str]
    fixture_name: str


@given("the plan-it artifact set is loaded")
def step_artifact_set_loaded(context: PlanContext) -> None:
    assert hasattr(context, "artifacts"), "artifacts not set - check environment.py"
    assert context.artifacts, "artifact set is empty - no plan files were written"


@then("the artifact set contains at least one plan issue file")
def step_contains_issue_file(context: PlanContext) -> None:
    issue_files = _issue_files(context)
    assert issue_files, (
        f"no task issue files found; artifacts: {sorted(context.artifacts)}"
    )


@then("the artifact set does not use PLAN_SUMMARY as a substitute")
def step_no_plan_summary_substitute(context: PlanContext) -> None:
    assert "PLAN_SUMMARY.md" not in context.artifacts, (
        "PLAN_SUMMARY.md is not a substitute for required tasks/issues/*.md files"
    )


@then("the artifact set contains no root-level issue markdown files")
def step_no_root_issue_markdown(context: PlanContext) -> None:
    root_markdown = [
        name
        for name in context.artifacts
        if name.endswith(".md") and "/" not in name and name != "CONTEXT.md"
    ]
    assert not root_markdown, (
        "issue and ADR files must be written under tasks/issues/ or docs/adrs/: "
        f"{root_markdown}"
    )


@then("every issue file uses the required filename format")
def step_issue_filename_format(context: PlanContext) -> None:
    invalid = [name for name in _issue_files(context) if not _ISSUE_PATH.match(name)]
    assert not invalid, (
        f"issue files must use tasks/issues/001-kebab-slug.md format: {invalid}"
    )


@then("every issue file has valid task frontmatter")
def step_valid_frontmatter(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        frontmatter = _extract_frontmatter(filename, content)
        fields = {
            match.group(1): match.group(2)
            for match in _FRONTMATTER_FIELD.finditer(frontmatter)
        }
        missing = _REQUIRED_FRONTMATTER_FIELDS - set(fields)
        assert not missing, f"{filename} missing frontmatter fields: {sorted(missing)}"
        assert fields["status"] == "active", f"{filename} status must be active"
        assert _DATE_VALUE.match(fields["created"]), (
            f"{filename} created date is not YYYY-MM-DD"
        )
        assert _DATE_VALUE.match(fields["updated"]), (
            f"{filename} updated date is not YYYY-MM-DD"
        )


@then("every issue file has all required task sections")
def step_has_required_sections(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        missing = [section for section in _REQUIRED_SECTIONS if section not in content]
        assert not missing, f"{filename} missing required sections: {missing}"


@then("every issue file has no template placeholders")
def step_no_placeholders(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        match = _PLACEHOLDER.search(content)
        assert match is None, (
            f"{filename} contains unresolved placeholder {match.group(0)!r}"
        )


@then("every issue file has no empty required sections")
def step_no_empty_sections(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        for section in _REQUIRED_SECTIONS:
            body = _section_body(content, section)
            assert body.strip(), f"{filename} section {section!r} is empty"


@then("every issue file has stable requirement and acceptance IDs")
def step_has_ids(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        assert _REQUIREMENT_ID.search(content), f"{filename} has no FR/NFR/OBS IDs"
        assert _ACCEPTANCE_ID.search(content), f"{filename} has no AC IDs"


@then("every issue file has AFK or HITL assignability with a reason")
def step_has_assignability(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        section = _section_body(content, "## Assignability")
        assert _ASSIGNABILITY.search(section), (
            f"{filename} lacks AFK/HITL with a specific reason"
        )


@then("every issue file has concrete dependencies")
def step_concrete_dependencies(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        section = _section_body(content, "## Dependencies")
        assert "-" in section, f"{filename} has no dependency entries"
        assert _VAGUE_DEPENDENCY.search(section) is None, (
            f"{filename} has vague dependencies"
        )


@then("every issue file has risk-scoped test entries")
def step_risk_scoped_tests(context: PlanContext) -> None:
    for filename, content in _issue_files(context).items():
        test_section = _section_body(content, "## Required Tests")
        assert _TEST_ID.search(test_section), f"{filename} has no stable test IDs"
        for reason in _NOT_APPLICABLE.findall(test_section):
            normalized = reason.strip().lower().rstrip(".")
            assert normalized not in _GENERIC_NOT_APPLICABLE_REASONS, (
                f"{filename} has generic Not applicable reason: {reason!r}"
            )


@then("architecture planning output includes an ADR stub when required")
def step_architecture_has_adr(context: PlanContext) -> None:
    if "architecture" not in context.fixture_name:
        return
    adr_files = _adr_files(context)
    assert adr_files, "architecture fixture should create at least one ADR stub"
    for filename, content in adr_files.items():
        assert "# ADR" in content or "## Decision" in content, (
            f"{filename} does not look like an ADR"
        )


@then("architecture planning issues link to the ADR dependency")
def step_architecture_links_adr(context: PlanContext) -> None:
    if "architecture" not in context.fixture_name:
        return
    combined = "\n".join(_issue_files(context).values())
    assert "docs/adrs/" in combined, (
        "architecture task dependencies do not link to an ADR"
    )


@then("routine planning output does not create ADR stubs")
def step_routine_has_no_adr(context: PlanContext) -> None:
    if "routine" not in context.fixture_name:
        return
    assert not _adr_files(context), (
        "routine validation fixture should not create ADR stubs"
    )


def _issue_files(context: PlanContext) -> dict[str, str]:
    return {
        name: content
        for name, content in context.artifacts.items()
        if _ISSUE_LOCATION.match(name)
    }


def _adr_files(context: PlanContext) -> dict[str, str]:
    return {
        name: content
        for name, content in context.artifacts.items()
        if _ADR_PATH.match(name)
    }


def _extract_frontmatter(filename: str, content: str) -> str:
    fences = list(_FRONTMATTER_FENCE.finditer(content))
    assert len(fences) >= 2, f"{filename} missing YAML frontmatter fences"
    assert fences[0].start() == 0, f"{filename} frontmatter must start at line 1"
    return content[fences[0].end() : fences[1].start()]


def _section_body(content: str, heading: str) -> str:
    start = content.find(heading)
    if start == -1:
        return ""
    after = content[start + len(heading) :]
    next_heading = re.search(r"^##\s", after, re.MULTILINE)
    return after[: next_heading.start()] if next_heading else after
