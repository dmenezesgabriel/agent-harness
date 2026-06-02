"""Behave step definitions for prd-it generated PRD validation."""

import re
from typing import Protocol

from behave import given, then  # type: ignore[import-untyped]

_PRD_PATH = re.compile(r"^docs/prd/[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_FRONTMATTER_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
_FRONTMATTER_FIELD = re.compile(r"^([\w-]+):\s*(.+?)\s*$", re.MULTILINE)
_DATE_VALUE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{[^}]+\}\}")
_NUMBER_OR_UNKNOWN = re.compile(r"\d|unknown|≥|<=|>=|under|zero", re.IGNORECASE)
_SOLUTION_LANGUAGE = re.compile(
    r"\b(?:we will build|the system should|the feature will|implement|architecture|database|api endpoint)\b",
    re.IGNORECASE,
)
_IMPLEMENTATION_LANGUAGE = re.compile(
    r"\b(?:database|schema|microservice|queue|cache|framework|react|django|rails|node\.js|api endpoint|graphql|rest endpoint|sql|migration|sdk)\b",
    re.IGNORECASE,
)

_REQUIRED_FRONTMATTER_FIELDS = {"id", "created", "updated", "status", "request-type"}
_REQUEST_TYPES = {"new-product", "new-feature", "behavior-change"}
_REQUIRED_SECTIONS = [
    "## Problem Statement",
    "## Personas",
    "## User Stories",
    "## Success Metrics",
    "## Constraints",
    "## Non-Goals",
    "## Open Questions",
]


class PrdContext(Protocol):
    artifacts: dict[str, str]
    current_file: str
    current_content: str


@given("the prd-it artifact set is loaded")
def step_artifact_set_loaded(context: PrdContext) -> None:
    assert hasattr(context, "artifacts"), "artifacts not set - check environment.py"
    assert context.artifacts, "artifact set is empty - no PRD file was written"


@given("the generated PRD is loaded")
def step_load_generated_prd(context: PrdContext) -> None:
    prd_files = _prd_files(context)
    assert prd_files, f"no PRD files found; artifacts: {sorted(context.artifacts)}"
    context.current_file, context.current_content = next(iter(prd_files.items()))


@then("the artifact set contains exactly one PRD file")
def step_contains_one_prd_file(context: PrdContext) -> None:
    prd_files = _prd_files(context)
    assert len(prd_files) == 1, (
        f"expected exactly one PRD file, found {sorted(prd_files)}"
    )


@then("the PRD has valid frontmatter")
def step_valid_frontmatter(context: PrdContext) -> None:
    frontmatter = _extract_frontmatter(context.current_file, context.current_content)
    fields = {
        match.group(1): match.group(2).strip('"')
        for match in _FRONTMATTER_FIELD.finditer(frontmatter)
    }
    missing = _REQUIRED_FRONTMATTER_FIELDS - set(fields)
    assert not missing, (
        f"{context.current_file} missing frontmatter fields: {sorted(missing)}"
    )
    assert fields["status"] == "draft", f"{context.current_file} status must be draft"
    assert fields["request-type"] in _REQUEST_TYPES, (
        f"{context.current_file} has invalid request-type"
    )
    assert _DATE_VALUE.match(fields["created"]), (
        f"{context.current_file} created date is not YYYY-MM-DD"
    )
    assert _DATE_VALUE.match(fields["updated"]), (
        f"{context.current_file} updated date is not YYYY-MM-DD"
    )


@then("the PRD has all required sections")
def step_has_required_sections(context: PrdContext) -> None:
    missing = [
        section
        for section in _REQUIRED_SECTIONS
        if section not in context.current_content
    ]
    assert not missing, f"{context.current_file} missing required sections: {missing}"
    for section in _REQUIRED_SECTIONS:
        assert _section_body(context.current_content, section).strip(), (
            f"{section} is empty"
        )


@then("the PRD has no template placeholders")
def step_no_placeholders(context: PrdContext) -> None:
    match = _PLACEHOLDER.search(context.current_content)
    assert match is None, (
        f"{context.current_file} contains placeholder {match.group(0)!r}"
    )


@then("the problem statement has no solution language")
def step_problem_no_solution_language(context: PrdContext) -> None:
    problem = _section_body(context.current_content, "## Problem Statement")
    match = _SOLUTION_LANGUAGE.search(problem)
    assert match is None, (
        f"problem statement contains solution language: {match.group(0)!r}"
    )


@then("the PRD includes at least one persona with a pain point")
def step_has_persona_with_pain(context: PrdContext) -> None:
    personas = _section_body(context.current_content, "## Personas")
    rows = [line for line in personas.splitlines() if line.strip().startswith("|")]
    data_rows = [row for row in rows if "---" not in row and "Persona" not in row]
    assert data_rows, "personas table has no persona rows"
    assert any(
        len([cell for cell in row.split("|") if cell.strip()]) >= 3 for row in data_rows
    ), "persona rows must include role/job-to-be-done and pain point"


@then("the PRD includes measurable success metrics")
def step_has_measurable_metrics(context: PrdContext) -> None:
    metrics = _section_body(context.current_content, "## Success Metrics")
    rows = [line for line in metrics.splitlines() if line.strip().startswith("|")]
    data_rows = [row for row in rows if "---" not in row and "Metric" not in row]
    assert data_rows, "success metrics table has no metric rows"
    assert all(_NUMBER_OR_UNKNOWN.search(row) for row in data_rows), (
        "each success metric row must include a baseline/target number or unknown baseline"
    )


@then("the PRD includes explicit non-goals")
def step_has_non_goals(context: PrdContext) -> None:
    non_goals = _section_body(context.current_content, "## Non-Goals")
    entries = [line for line in non_goals.splitlines() if line.strip().startswith("-")]
    assert entries, "non-goals section must include at least one explicit non-goal"
    assert not any(
        line.strip().lower() in {"- out of scope", "- none", "- n/a"}
        for line in entries
    ), "non-goals must be explicit, not generic"


@then("the PRD contains no architecture or implementation details")
def step_no_implementation_details(context: PrdContext) -> None:
    content_without_constraints = context.current_content.replace(
        _section_body(context.current_content, "## Constraints"), ""
    )
    match = _IMPLEMENTATION_LANGUAGE.search(content_without_constraints)
    assert match is None, f"PRD contains implementation detail: {match.group(0)!r}"


def _prd_files(context: PrdContext) -> dict[str, str]:
    return {
        name: content
        for name, content in context.artifacts.items()
        if _PRD_PATH.match(name)
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
