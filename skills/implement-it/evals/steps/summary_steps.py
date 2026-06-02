"""Behave step definitions for implement-it implementation summary validation."""

import re
from typing import Protocol

from behave import given, then  # type: ignore[import-untyped]

_FRONTMATTER_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
_DATE_VALUE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_FIELD = re.compile(
    r"^(?:created|updated):\s*['\"]?(.+?)['\"]?\s*$", re.MULTILINE
)
_FRONTMATTER_FIELD = re.compile(r"^(\w+):\s*.+", re.MULTILINE)

_REQUIRED_FRONTMATTER_FIELDS = {"id", "issue", "created", "updated"}

_REQUIRED_SECTIONS = [
    "## Related Task",
    "## Files Changed",
    "## Behavior Implemented",
    "## Design Notes",
    "## Tests Added or Updated",
    "## Test Categories Not Applicable",
    "## Validation Run",
    "## Accessibility Notes",
    "## Observability Changes",
    "## ADR Updates",
    "## Unresolved Assumptions or Follow-Up",
]

_SOURCE_EXTENSIONS = {
    ".c",
    ".cs",
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}

_SOURCE_ROOTS = (
    "app/",
    "cmd/",
    "internal/",
    "lib/",
    "packages/",
    "server/",
    "src/",
)

_TEST_MARKERS = ("/test/", "/tests/", "tests/", "test/")


class SummaryContext(Protocol):
    artifacts: dict[str, str]
    current_file: str
    current_content: str


def _extract_frontmatter(content: str) -> str | None:
    """Return the text between the opening and closing --- fences, or None."""
    fences = [m.start() for m in _FRONTMATTER_FENCE.finditer(content)]
    if len(fences) < 2:
        return None
    start = fences[0] + content[fences[0] :].index("\n") + 1
    return content[start : fences[1]]


def _section_content_after(content: str, heading: str) -> str:
    """Return everything between `heading` and the next ## heading (or EOF)."""
    idx = content.find(heading)
    if idx == -1:
        return ""
    after = content[idx + len(heading) :]
    next_section = re.search(r"^##\s", after, re.MULTILINE)
    return after[: next_section.start()] if next_section else after


@given("the implement-it artifact set is loaded")
def step_artifact_set_loaded(context: SummaryContext) -> None:
    assert hasattr(context, "artifacts"), (
        "context.artifacts not populated — check environment.py before_scenario hook"
    )


@given('the implementation summary "{filename}"')
def step_load_summary(context: SummaryContext, filename: str) -> None:
    content = context.artifacts.get(filename)
    assert content is not None, f"artifact {filename!r} not found in fixture set"
    context.current_file = filename
    context.current_content = content


@given("the generated implementation summary is loaded")
def step_load_generated_summary(context: SummaryContext) -> None:
    """Find the first .md artifact whose content starts with a frontmatter fence."""
    for name, content in context.artifacts.items():
        if name.endswith(".md") and _FRONTMATTER_FENCE.search(content):
            context.current_file = name
            context.current_content = content
            return
    raise AssertionError(
        "no markdown artifact with YAML frontmatter found in generated artifacts; "
        "expected the skill to produce an implementation summary"
    )


@then("the artifact set contains at least one markdown file")
def step_has_markdown_artifact(context: SummaryContext) -> None:
    md_files = [n for n in context.artifacts if n.endswith(".md")]
    assert md_files, (
        "no .md file found in generated artifacts; "
        "implement-it must produce an implementation summary"
    )


@then("the artifact set contains at least one implementation source file")
def step_has_source_artifact(context: SummaryContext) -> None:
    source_files = [name for name in context.artifacts if _is_source_file(name)]
    assert source_files, (
        "no implementation source file found in generated artifacts; "
        "expected code under a source root such as src/, app/, lib/, or internal/"
    )


@then("the artifact set contains at least one test file")
def step_has_test_artifact(context: SummaryContext) -> None:
    test_files = [name for name in context.artifacts if _is_test_file(name)]
    assert test_files, (
        "no test file found in generated artifacts; "
        "expected tests under tests/ or test/, or files named test_* / *.test.*"
    )


@then("the summary has valid YAML frontmatter")
def step_has_frontmatter(context: SummaryContext) -> None:
    fences = list(_FRONTMATTER_FENCE.finditer(context.current_content))
    assert len(fences) >= 2, (
        f"{context.current_file!r} is missing YAML frontmatter; "
        "expected opening and closing '---' fences at the top of the file"
    )
    assert fences[0].start() == 0, (
        f"{context.current_file!r} frontmatter does not start at line 1; "
        f"'---' found at position {fences[0].start()} instead of 0"
    )


@then("the summary frontmatter has all required fields")
def step_frontmatter_has_required_fields(context: SummaryContext) -> None:
    fm = _extract_frontmatter(context.current_content)
    assert fm is not None, f"{context.current_file!r} has no parseable frontmatter"
    present = {m.group(1) for m in _FRONTMATTER_FIELD.finditer(fm)}
    missing = _REQUIRED_FRONTMATTER_FIELDS - present
    assert not missing, (
        f"{context.current_file!r} frontmatter is missing required fields: "
        f"{sorted(missing)}; present fields: {sorted(present)}"
    )


@then("the summary frontmatter has invalid date format")
def step_frontmatter_has_bad_date(context: SummaryContext) -> None:
    """Assert that at least one date field uses a non-YYYY-MM-DD value (for invalid fixtures)."""
    fm = _extract_frontmatter(context.current_content)
    assert fm is not None, f"{context.current_file!r} has no parseable frontmatter"
    date_matches = _DATE_FIELD.findall(fm)
    bad = [v for v in date_matches if not _DATE_VALUE.match(v.strip())]
    assert bad, (
        f"{context.current_file!r} all date fields use valid YYYY-MM-DD format; "
        "expected at least one to be malformed for this negative fixture"
    )


@then("the summary frontmatter is missing required fields")
def step_frontmatter_missing_fields(context: SummaryContext) -> None:
    """Assert that at least one required field is absent (for invalid fixtures)."""
    fm = _extract_frontmatter(context.current_content)
    if fm is None:
        return  # no frontmatter at all counts as missing fields
    present = {m.group(1) for m in _FRONTMATTER_FIELD.finditer(fm)}
    missing = _REQUIRED_FRONTMATTER_FIELDS - present
    assert missing, (
        f"{context.current_file!r} has all required frontmatter fields; "
        f"expected at least one to be missing for this negative fixture"
    )


@then("the summary has all required sections")
def step_has_all_sections(context: SummaryContext) -> None:
    missing = [h for h in _REQUIRED_SECTIONS if h not in context.current_content]
    assert not missing, (
        f"{context.current_file!r} is missing required section headings: "
        f"{missing}"
    )


@then("the summary is missing required sections")
def step_missing_required_sections(context: SummaryContext) -> None:
    absent = [h for h in _REQUIRED_SECTIONS if h not in context.current_content]
    assert absent, (
        f"{context.current_file!r} has all required sections; "
        "expected at least one to be missing for this negative fixture"
    )


@then("the summary validation run is not empty")
def step_validation_run_not_empty(context: SummaryContext) -> None:
    section = _section_content_after(context.current_content, "## Validation Run")
    assert section.strip(), (
        f"{context.current_file!r} '## Validation Run' section is empty; "
        "must contain at least one command with its result"
    )
    # Must contain something beyond a bare N/A or placeholder
    meaningful = section.strip().lower()
    assert meaningful not in {"n/a", "none", "n/a.", "none."}, (
        f"{context.current_file!r} '## Validation Run' contains only '{section.strip()}'; "
        "must include at least one concrete command"
    )


def _is_source_file(name: str) -> bool:
    path = name.replace("\\", "/")
    if _is_test_file(path) or path.startswith("tasks/implementation/"):
        return False
    if not path.startswith(_SOURCE_ROOTS):
        return False
    return _extension(path) in _SOURCE_EXTENSIONS


def _is_test_file(name: str) -> bool:
    path = name.replace("\\", "/")
    filename = path.rsplit("/", 1)[-1]
    if _extension(path) not in _SOURCE_EXTENSIONS:
        return False
    return (
        any(marker in path for marker in _TEST_MARKERS)
        or filename.startswith("test_")
        or ".test." in filename
        or ".spec." in filename
    )


def _extension(path: str) -> str:
    filename = path.rsplit("/", 1)[-1]
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1]
