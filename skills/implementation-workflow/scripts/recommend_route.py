#!/usr/bin/env python3
import argparse
import json
import re
import sys

ROUTES = {
    "backend-tdd": ["api", "backend", "service", "repository", "domain", "rule", "validation", "invariant", "persistence"],
    "frontend-component-driven": ["ui", "screen", "component", "form", "button", "modal", "accessibility", "keyboard", "visible state"],
    "fullstack-seam-splitting": ["end-to-end", "fullstack", "frontend and backend", "ui and api", "contract", "flow across"],
    "bugfix-workflow": ["bug", "fix", "broken", "regression", "repro", "incorrect", "crash", "failing"],
    "refactor-workflow": ["refactor", "cleanup", "restructure", "rename", "decouple", "technical debt", "preserve behavior"],
}

PRIORITY = [
    "bugfix-workflow",
    "refactor-workflow",
    "fullstack-seam-splitting",
    "frontend-component-driven",
    "backend-tdd",
]


def contains_term(text, term):
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def matched_keywords(text, keywords):
    lowered = text.lower()
    return [kw for kw in keywords if contains_term(lowered, kw)]


def main():
    parser = argparse.ArgumentParser(description="Recommend a lightweight implementation route.")
    parser.add_argument("text", nargs="?", help="Scoped implementation change description.")
    parser.add_argument("--text", dest="text_flag", help="Scoped implementation change description.")
    args = parser.parse_args()

    text = args.text_flag or args.text
    if not text:
        print("error: provide change text as an argument or with --text", file=sys.stderr)
        return 2

    hits = {route: matched_keywords(text, words) for route, words in ROUTES.items()}
    hits = {route: words for route, words in hits.items() if words}

    route = "backend-tdd"
    if hits.get("frontend-component-driven") and hits.get("backend-tdd"):
        route = "fullstack-seam-splitting"
        hits.setdefault("fullstack-seam-splitting", []).append("inferred-from-frontend-and-backend-signals")
    else:
        for candidate in PRIORITY:
            if candidate in hits:
                route = candidate
                break

    reasons = []
    if route == "backend-tdd":
        reasons.append("Domain, API, rule, or persistence language suggests a backend-owned change.")
    elif route == "frontend-component-driven":
        reasons.append("User-visible behavior or accessibility language suggests leading with frontend behavior scenarios.")
    elif route == "fullstack-seam-splitting":
        reasons.append("The request crosses the frontend/backend seam, so define the contract first.")
    elif route == "bugfix-workflow":
        reasons.append("Bugfix or regression language suggests reproducing the failure and adding protection first.")
    elif route == "refactor-workflow":
        reasons.append("Refactor language suggests protecting current behavior before restructuring.")

    result = {
        "route": route,
        "signals": hits,
        "reasons": reasons,
    }
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
