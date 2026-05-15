# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

ISSUE_KEYWORDS: dict[str, list[str]] = {
    "bugfix": ["bug", "fix", "broken", "error", "regression", "crash", "incorrect", "failing"],
    "refactor": ["refactor", "cleanup", "restructure", "rename", "simplify", "technical debt", "decouple"],
    "feature": ["add", "new", "support", "enable", "allow", "create", "introduce", "feature"],
    "improvement": ["improve", "optimize", "enhance", "better", "reduce", "streamline", "polish"],
}

SURFACE_KEYWORDS: dict[str, list[str]] = {
    "frontend": ["ui", "frontend", "button", "form", "page", "screen", "modal", "component", "accessibility", "keyboard"],
    "backend": ["api", "backend", "database", "service", "endpoint", "job", "queue", "migration", "auth", "authorization"],
}

ISSUE_TYPE_PRIORITY: list[str] = ["bugfix", "refactor", "feature", "improvement"]


def contains_term(text: str, term: str) -> bool:
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def score_text(text: str, mapping: dict[str, list[str]]) -> dict[str, list[str]]:
    lowered = text.lower()
    return {
        label: [kw for kw in keywords if contains_term(lowered, kw)]
        for label, keywords in mapping.items()
        if any(contains_term(lowered, kw) for kw in keywords)
    }


def choose_issue_type(type_hits: dict[str, list[str]]) -> str:
    for label in ISSUE_TYPE_PRIORITY:
        if label in type_hits:
            return label
    return "improvement"


def choose_surface(surface_hits: dict[str, list[str]]) -> str:
    frontend = surface_hits.get("frontend", [])
    backend = surface_hits.get("backend", [])
    if frontend and backend:
        return "fullstack"
    if frontend:
        return "frontend"
    if backend:
        return "backend"
    return "unspecified"


def build_tags(type_hits: dict[str, list[str]], surface_hits: dict[str, list[str]]) -> list[str]:
    return sorted(
        ({choose_issue_type(type_hits), choose_surface(surface_hits)}
         | set(type_hits.keys()) | set(surface_hits.keys()))
        - {"unspecified"}
    )


def mentions_scope(text: str) -> bool:
    terms = ["acceptance criteria", "scope", "non-goal", "ready", "definition of done"]
    lowered = text.lower()
    return any(contains_term(lowered, term) for term in terms)


def classify(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    type_hits = score_text(normalized, ISSUE_KEYWORDS)
    surface_hits = score_text(normalized, SURFACE_KEYWORDS)
    return {
        "issue_type": choose_issue_type(type_hits),
        "surface": choose_surface(surface_hits),
        "tags": build_tags(type_hits, surface_hits),
        "signals": {
            "issue_type": type_hits,
            "surface": surface_hits,
            "mentions_acceptance_or_scope": mentions_scope(normalized),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer lightweight issue classification signals.")
    parser.add_argument("text", nargs="?", help="Issue text to classify.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.text:
        print("error: provide issue text as a positional argument", file=sys.stderr)
        return 2
    result = classify(args.text)
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
