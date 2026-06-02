import re
from typing import Protocol

from behave import given, then

_PASS_RATE_PATTERN = re.compile(r"\*\*Pass rate\*\*: \d+/\d+ \(\d+%\)")


class ReportContext(Protocol):
    artifacts: dict[str, str]
    current_file: str
    current_content: str


@given("the skill-evaluator artifact set is loaded")
def step_artifact_set_loaded(context: ReportContext) -> None:
    assert hasattr(context, "artifacts"), "artifacts not set - check environment.py"
    assert context.artifacts, "artifact set is empty - no fixture files found"


@given('the evaluator report "{filename}"')
def step_load_report(context: ReportContext, filename: str) -> None:
    content = context.artifacts.get(filename)
    assert content is not None, (
        f"report {filename!r} not found; available: {sorted(context.artifacts)}"
    )
    context.current_file = filename
    context.current_content = content


@then("the report identifies the evaluated skill and mode")
def step_report_identifies_skill_and_mode(context: ReportContext) -> None:
    assert "# Eval Report:" in context.current_content, (
        f"{context.current_file!r} is missing '# Eval Report:' heading"
    )
    assert "Mode:" in context.current_content, (
        f"{context.current_file!r} is missing run mode metadata"
    )


@then("the report includes structural checks")
def step_report_includes_structural_checks(context: ReportContext) -> None:
    assert "## Structural checks (behave)" in context.current_content, (
        f"{context.current_file!r} is missing structural check results"
    )


@then("the report includes skill input size")
def step_report_includes_input_size(context: ReportContext) -> None:
    assert "## Skill input size" in context.current_content, (
        f"{context.current_file!r} is missing skill input size evidence"
    )


@then("the report is missing skill input size")
def step_report_missing_input_size(context: ReportContext) -> None:
    assert "## Skill input size" not in context.current_content, (
        f"{context.current_file!r} unexpectedly includes skill input size evidence"
    )


@then("the report includes pass rate")
def step_report_includes_pass_rate(context: ReportContext) -> None:
    assert _PASS_RATE_PATTERN.search(context.current_content), (
        f"{context.current_file!r} is missing a formatted pass rate"
    )
