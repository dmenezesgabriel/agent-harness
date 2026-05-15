#!/usr/bin/env python3
import argparse
import json
import re
import sys

ISSUE_KEYWORDS = {
    "bugfix": ["bug", "fix", "broken", "error", "regression", "crash", "incorrect", "failing"],
    "refactor": ["refactor", "cleanup", "restructure", "rename", "simplify", "technical debt", "decouple"],
    "feature": ["add", "new", "support", "enable", "allow", "create", "introduce", "feature"],
    "improvement": ["improve", "optimize", "enhance", "better", "reduce", "streamline", "polish"],
}

SURFACE_KEYWORDS = {
    "frontend": ["ui", "frontend", "button", "form", "page", "screen", "modal", "component", "accessibility", "keyboard"],
    "backend": ["api", "backend", "database", "service", "endpoint", "job", "queue", "migration", "auth", "authorization"],
}


def contains_term(text, term):
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def score_text(text, mapping):
    lowered = text.lower()
    hits = {}
    for label, keywords in mapping.items():
        matched = [kw for kw in keywords if contains_term(lowered, kw)]
        if matched:
            hits[label] = matched
    return hits


def choose_issue_type(type_hits):
    priority = ["bugfix", "refactor", "feature", "improvement"]
    for label in priority:
        if label in type_hits:
            return label
    return "improvement"


def choose_surface(surface_hits):
    frontend = surface_hits.get("frontend", [])
    backend = surface_hits.get("backend", [])
    if frontend and backend:
        return "fullstack"
    if frontend:
        return "frontend"
    if backend:
        return "backend"
    return "unspecified"


def main():
    parser = argparse.ArgumentParser(description="Infer lightweight issue classification signals.")
    parser.add_argument("text", nargs="?", help="Issue/request text to classify.")
    parser.add_argument("--text", dest="text_flag", help="Issue/request text to classify.")
    args = parser.parse_args()

    text = args.text_flag or args.text
    if not text:
        print("error: provide issue text as an argument or with --text", file=sys.stderr)
        return 2

    normalized = re.sub(r"\s+", " ", text).strip()
    type_hits = score_text(normalized, ISSUE_KEYWORDS)
    surface_hits = score_text(normalized, SURFACE_KEYWORDS)

    result = {
        "issue_type": choose_issue_type(type_hits),
        "surface": choose_surface(surface_hits),
        "tags": sorted(set([choose_issue_type(type_hits), choose_surface(surface_hits)] + list(type_hits.keys()) + list(surface_hits.keys())) - {"unspecified"}),
        "signals": {
            "issue_type": type_hits,
            "surface": surface_hits,
            "mentions_acceptance_or_scope": any(contains_term(normalized.lower(), term) for term in ["acceptance criteria", "scope", "non-goal", "ready", "definition of done"]),
        },
    }

    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
