#!/usr/bin/env python3
import argparse
import json
import re
import sys

CHECKS = {
    "targeted_tests": "Run the smallest targeted unit/component/regression tests for touched behavior.",
    "integration_checks": "Run the nearest integration or seam-level checks.",
    "type_checks": "Run type checking when the project uses it.",
    "lint": "Run lint only when enforced or commonly relevant to this area.",
    "build_checks": "Run build/package checks when compilation, bundling, or packaging may be affected.",
    "accessibility_checks": "Verify roles, labels, keyboard, focus, and error states for changed UI behavior.",
    "contract_checks": "Verify request/response or message contract compatibility.",
    "security_scan": "Run a focused security scan such as semgrep when the change touches a trust boundary.",
    "dependency_audit": "Run ecosystem dependency audit tools for dependency updates or supply-chain risk.",
}


def contains_term(text, term):
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def has_any(text, terms):
    return any(contains_term(text, term) for term in terms)


def main():
    parser = argparse.ArgumentParser(description="Select a minimal validation plan from change/risk text.")
    parser.add_argument("text", nargs="?", help="Change/risk text to analyze.")
    parser.add_argument("--text", dest="text_flag", help="Change/risk text to analyze.")
    args = parser.parse_args()

    text = (args.text_flag or args.text or "").lower().strip()
    if not text:
        print("error: provide change/risk text as an argument or with --text", file=sys.stderr)
        return 2

    selected = ["targeted_tests"]
    reasons = ["Always start with the smallest targeted tests for the changed behavior."]
    optional_commands = []

    if has_any(text, ["frontend", "ui", "component", "form", "modal", "screen", "accessibility", "keyboard"]):
        selected.append("accessibility_checks")
        reasons.append("The change affects user-visible behavior or accessibility-sensitive UI states.")

    if has_any(text, ["api", "contract", "schema", "request", "response", "message"]):
        selected.append("contract_checks")
        reasons.append("The change touches a contract boundary that should be verified explicitly.")

    if has_any(text, ["integration", "database", "persistence", "migration", "queue", "auth", "authorization", "backend", "service"]):
        selected.append("integration_checks")
        reasons.append("The change crosses a backend or seam boundary where unit checks alone may miss regressions.")

    if has_any(text, ["typescript", "python", "type", "typed", "schema"]):
        selected.append("type_checks")
        reasons.append("Type-aware tooling is likely relevant to this change.")

    if has_any(text, ["build", "bundle", "compile", "packaging", "config", "ci"]):
        selected.append("build_checks")
        reasons.append("Build or configuration changes justify a compile/package check.")

    if has_any(text, ["lint", "style", "format"]):
        selected.append("lint")
        reasons.append("The request explicitly mentions lint/style-sensitive validation.")

    if has_any(text, ["auth", "authorization", "secret", "token", "payment", "sensitive", "external input", "file upload", "trust boundary"]):
        selected.append("security_scan")
        reasons.append("The change touches a trust boundary or sensitive path, so a focused security scan is justified.")
        optional_commands.append("semgrep --config auto")

    if has_any(text, ["dependency", "upgrade", "bump", "package.json", "requirements", "lockfile"]):
        selected.append("dependency_audit")
        reasons.append("Dependency changes justify an ecosystem audit in addition to targeted tests.")
        optional_commands.extend(["pnpm audit", "npm audit", "pip-audit"])

    deduped = []
    for item in selected:
        if item not in deduped:
            deduped.append(item)

    result = {
        "selected_checks": [{"name": name, "description": CHECKS[name]} for name in deduped],
        "reasons": reasons,
        "optional_commands": optional_commands,
    }

    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
