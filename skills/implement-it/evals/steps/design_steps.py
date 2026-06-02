"""Behave step definitions for implement-it design decision validation."""

import re
from typing import Protocol

from behave import then  # type: ignore[import-untyped]


class DesignSummaryContext(Protocol):
    artifacts: dict[str, str]
    current_file: str
    current_content: str


_REQUIRED_PRINCIPLES = [
    "Single Responsibility",
    "Open/Closed",
    "Liskov Substitution",
    "Interface Segregation",
    "Dependency Inversion",
]

_SOLID_KEYWORDS = _REQUIRED_PRINCIPLES + [
    "SRP",
    "OCP",
    "LSP",
    "ISP",
    "DIP",
    "SOLID",
]

_PATTERN_KEYWORDS = [
    "Adapter",
    "Strategy",
    "Factory",
    "Facade",
    "Decorator",
    "Composite",
    "Observer",
    "Command",
    "Template Method",
    "Chain of Responsibility",
    "Builder",
    "Singleton",
    "Abstract Factory",
    "Proxy",
    "Bridge",
    "Flyweight",
    "Mediator",
    "Memento",
    "State",
    "Visitor",
    "Interpreter",
]


def _section_content_after(content: str, heading: str) -> str:
    """Return everything between heading and the next ## heading (or EOF)."""
    idx = content.find(heading)
    if idx == -1:
        return ""
    after = content[idx + len(heading) :]
    next_section = re.search(r"^##\s", after, re.MULTILINE)
    return after[: next_section.start()] if next_section else after


def _design_notes(content: str) -> str:
    return _section_content_after(content, "## Design Notes")


@then('the design notes name a SOLID principle')
def step_design_notes_name_principle(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    matches = [kw for kw in _SOLID_KEYWORDS if kw.lower() in notes.lower()]
    assert matches, (
        f"{context.current_file!r} Design Notes do not name any SOLID principle; "
        f"expected at least one of {_SOLID_KEYWORDS}"
    )


@then('the design notes reference the "{pattern_name}" pattern')
def step_design_notes_reference_pattern(
    context: DesignSummaryContext, pattern_name: str
) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    assert pattern_name.lower() in notes.lower(), (
        f"{context.current_file!r} Design Notes do not reference the "
        f"'{pattern_name}' pattern; content: {notes.strip()[:200]}"
    )


@then("the design notes explain WHY the principle was chosen")
def step_design_notes_explain_why(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    why_keywords = [
        "because",
        "reason",
        "avoids",
        "eliminates",
        "eliminated",
        "removes",
        "removed",
        "keeps",
        "allows",
        "enables",
        "prevents",
        "protects",
        "follows",
        "makes",
        "ensures",
    ]
    matches = [kw for kw in why_keywords if kw.lower() in notes.lower()]
    assert matches, (
        f"{context.current_file!r} Design Notes state WHAT was chosen but not WHY; "
        f"expected a justification keyword like 'because', 'avoids', 'eliminates'"
    )


@then("the design notes explicitly justify why no design pattern was needed")
def step_design_notes_justify_avoidance(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    avoidance_keywords = [
        "no design pattern",
        "no solid",
        "not needed",
        "no change pressure",
        "no volatility",
        "no reason",
        "overengineering",
        "over-engineering",
        "would be overengineering",
        "single-file",
        "zero-dependency",
        "no abstraction needed",
        "no principle",
        "no pattern",
        "not justified",
    ]
    matches = [kw for kw in avoidance_keywords if kw.lower() in notes.lower()]
    assert matches, (
        f"{context.current_file!r} Design Notes do not explicitly justify "
        f"why no pattern was needed; expected a phrase like 'no change pressure' or "
        f"'would be overengineering'"
    )


@then("the design notes apply a pattern without a valid reason")
def step_design_notes_unjustified_pattern(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    pattern_refs = [kw for kw in _PATTERN_KEYWORDS if kw.lower() in notes.lower()]
    assert pattern_refs, (
        f"{context.current_file!r} Design Notes do not reference any design pattern; "
        f"expected at least one pattern reference for this negative fixture"
    )
    reason_keywords = [
        "because",
        "reason",
        "avoids",
        "change pressure",
        "volatility",
        "justified",
        "needed",
    ]
    has_reason = any(kw.lower() in notes.lower() for kw in reason_keywords)
    assert not has_reason, (
        f"{context.current_file!r} Design Notes include a pattern with reasoning; "
        f"expected a pattern applied without justification for this negative fixture"
    )


@then("the generated design notes contain design reasoning")
def step_generated_design_reasoning(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    has_principle = any(kw.lower() in notes.lower() for kw in _SOLID_KEYWORDS)
    has_avoidance = any(
        kw.lower() in notes.lower()
        for kw in ["no pattern", "no design", "not needed", "overengineering",
                    "no change pressure", "no volatility", "no principle"]
    )
    has_reason = any(
        kw.lower() in notes.lower()
        for kw in ["because", "reason", "avoids", "allows", "enables",
                    "prevents", "keeps", "protects"]
    )
    assert (has_principle or has_avoidance) and has_reason, (
        f"{context.current_file!r} Design Notes lack design reasoning; "
        f"expected either a SOLID principle or an explicit avoidance, "
        f"each paired with a reason why"
    )


@then("the generated design notes contain a pattern reference or explicit avoidance")
def step_generated_pattern_or_avoidance(context: DesignSummaryContext) -> None:
    notes = _design_notes(context.current_content)
    assert notes, (
        f"{context.current_file!r} has no '## Design Notes' section"
    )
    has_pattern = any(kw.lower() in notes.lower() for kw in _PATTERN_KEYWORDS)
    has_avoidance = any(
        kw.lower() in notes.lower()
        for kw in ["no pattern", "overengineering", "not needed",
                    "no volatility", "no change pressure"]
    )
    assert has_pattern or has_avoidance, (
        f"{context.current_file!r} Design Notes neither reference a design pattern "
        f"nor explicitly justify avoiding one; expected one or the other"
    )
