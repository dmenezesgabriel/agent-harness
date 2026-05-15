# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
# ///

"""Validate an Agent Skill directory.

Usage:
  uv run scripts/validate_skill.py --skill-dir .
  uv run scripts/validate_skill.py --skill-dir . --format json
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(level=logging.INFO, format="%(message)s")


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INLINE_PATH_RE = re.compile(
    r"`((?:scripts|references|assets|evals)/[^`]+?)`"
)


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str = "SKILL.md"


def add(
    findings: list[Finding],
    level: str,
    code: str,
    message: str,
    path: str = "SKILL.md",
) -> None:
    findings.append(Finding(level=level, code=code, message=message, path=path))


def parse_skill_md(skill_md: Path, findings: list[Finding]) -> tuple[dict[str, Any] | None, str]:
    if not skill_md.exists():
        add(findings, "ERROR", "missing-skill-md", "Required file SKILL.md was not found.")
        return None, ""

    text = skill_md.read_text(encoding="utf-8")

    if not text.startswith("---\n"):
        add(findings, "ERROR", "missing-frontmatter", "SKILL.md must start with YAML frontmatter delimited by ---.")
        return None, text

    closing = text.find("\n---", 4)
    if closing == -1:
        add(findings, "ERROR", "unclosed-frontmatter", "YAML frontmatter is missing a closing --- delimiter.")
        return None, text

    frontmatter_text = text[4:closing].strip()
    body = text[closing + len("\n---") :].strip()

    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        add(findings, "ERROR", "invalid-yaml", f"Frontmatter is not valid YAML: {exc}")
        return None, body

    if not isinstance(data, dict):
        add(findings, "ERROR", "frontmatter-not-mapping", "Frontmatter must be a YAML mapping.")
        return None, body

    if not body:
        add(findings, "ERROR", "empty-body", "SKILL.md body must not be empty.")

    return data, body


def validate_name(data: dict[str, Any], skill_dir: Path, findings: list[Finding]) -> None:
    name = data.get("name")

    if name is None:
        add(findings, "ERROR", "missing-name", "Required frontmatter field `name` is missing.")
        return

    if not isinstance(name, str):
        add(findings, "ERROR", "name-not-string", "`name` must be a string.")
        return

    if not (1 <= len(name) <= 64):
        add(findings, "ERROR", "name-length", f"`name` must be 1-64 characters (received {len(name)}).")

    if not NAME_RE.match(name):
        add(
            findings,
            "ERROR",
            "name-format",
            "`name` must contain only lowercase letters, numbers, and single hyphens; it must not start/end with a hyphen or contain consecutive hyphens.",
        )

    if name != skill_dir.name:
        add(
            findings,
            "ERROR",
            "name-directory-mismatch",
            f"`name` must match parent directory name. Found name={name!r}, directory={skill_dir.name!r}.",
        )


def validate_description(data: dict[str, Any], findings: list[Finding]) -> None:
    description = data.get("description")

    if description is None:
        add(findings, "ERROR", "missing-description", "Required frontmatter field `description` is missing.")
        return

    if not isinstance(description, str):
        add(findings, "ERROR", "description-not-string", "`description` must be a string.")
        return

    stripped = description.strip()
    if not stripped:
        add(findings, "ERROR", "empty-description", "`description` must be non-empty.")

    if len(description) > 1024:
        add(findings, "ERROR", "description-too-long", f"`description` must be at most 1024 characters (received {len(description)}).")

    if len(stripped) < 40:
        add(
            findings,
            "WARNING",
            "description-too-short",
            "`description` may be too vague; describe what the skill does and when to use it.",
        )

    lowered = stripped.lower()
    if "use" not in lowered and "when" not in lowered:
        add(
            findings,
            "WARNING",
            "description-not-activation-oriented",
            "Prefer activation-oriented phrasing such as: `Use this skill when...`.",
        )


def validate_optional_fields(data: dict[str, Any], findings: list[Finding]) -> None:
    license_value = data.get("license")
    if license_value is not None and not isinstance(license_value, str):
        add(findings, "ERROR", "license-not-string", "`license`, if provided, must be a string.")

    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            add(findings, "ERROR", "compatibility-not-string", "`compatibility`, if provided, must be a string.")
        elif not (1 <= len(compatibility) <= 500):
            add(findings, "ERROR", "compatibility-length", "`compatibility` must be 1-500 characters if provided.")

    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        add(findings, "ERROR", "metadata-not-mapping", "`metadata`, if provided, must be a mapping.")

    allowed_tools = data.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        add(findings, "ERROR", "allowed-tools-not-string", "`allowed-tools`, if provided, must be a space-separated string.")


def validate_body(body: str, findings: list[Finding]) -> None:
    if not body:
        return

    if len(body.splitlines()) > 500:
        add(
            findings,
            "WARNING",
            "body-too-long",
            "SKILL.md is over 500 lines; consider moving detailed material into references/ or assets/.",
        )

    recommended_headings = ["purpose", "workflow"]
    body_lower = body.lower()
    for heading in recommended_headings:
        if f"## {heading}" not in body_lower:
            add(
                findings,
                "INFO",
                f"missing-{heading}-section",
                f"Consider adding a `## {heading.title()}` section.",
            )

    if "references/" in body and "when" not in body_lower:
        add(
            findings,
            "WARNING",
            "unclear-reference-loading",
            "When referencing files in references/, tell the agent exactly when to load each file.",
        )


def validate_referenced_paths(skill_dir: Path, body: str, findings: list[Finding]) -> None:
    for match in INLINE_PATH_RE.finditer(body):
        raw = match.group(1).strip()
        clean = raw.split()[0].rstrip(".,:;)")

        if clean.startswith("/"):
            add(
                findings,
                "ERROR",
                "absolute-support-path",
                f"Support file path should be relative to skill root, not absolute: {raw}",
            )
            continue

        target = skill_dir / clean
        if not target.exists():
            add(
                findings,
                "WARNING",
                "referenced-file-missing",
                f"Referenced support file does not exist: {clean}",
            )


def validate_scripts(skill_dir: Path, findings: list[Finding]) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return

    for script in scripts_dir.iterdir():
        if script.is_dir():
            continue

        if script.suffix == ".py":
            text = script.read_text(encoding="utf-8", errors="replace")

            if "argparse" not in text:
                add(
                    findings,
                    "WARNING",
                    "python-script-without-argparse",
                    f"Python script should use argparse: {script.relative_to(skill_dir)}",
                    path=str(script.relative_to(skill_dir)),
                )

            if "dependencies = [" in text and "# /// script" not in text:
                add(
                    findings,
                    "WARNING",
                    "invalid-pep723-shape",
                    f"Python script appears to declare dependencies but lacks PEP 723 script metadata markers: {script.relative_to(skill_dir)}",
                    path=str(script.relative_to(skill_dir)),
                )

            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                        add(
                            findings,
                            "ERROR",
                            "interactive-python-script",
                            f"Scripts must be non-interactive; avoid input(): {script.relative_to(skill_dir)}",
                            path=str(script.relative_to(skill_dir)),
                        )
                        break
            except SyntaxError:
                pass


def render_text(findings: list[Finding]) -> str:
    if not findings:
        return "PASS: no findings."

    lines: list[str] = []
    for finding in findings:
        lines.append(f"{finding.level}: {finding.code}: {finding.path}: {finding.message}")
    return "\n".join(lines)


def render_json(findings: list[Finding]) -> str:
    errors = sum(1 for item in findings if item.level == "ERROR")
    warnings = sum(1 for item in findings if item.level == "WARNING")
    infos = sum(1 for item in findings if item.level == "INFO")
    payload = {
        "ok": errors == 0,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "total": len(findings),
        },
        "findings": [asdict(item) for item in findings],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory.",
        epilog=(
            "Examples:\n"
            "  uv run scripts/validate_skill.py --skill-dir .\n"
            "  uv run scripts/validate_skill.py --skill-dir . --format json\n\n"
            "Exit codes:\n"
            "  0  All checks passed (no errors)\n"
            "  1  At least one error found"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill-dir",
        type=Path,
        required=True,
        help="Path to the skill directory containing SKILL.md.",
    )
    parser.add_argument(
        "--format", dest="output_format",
        choices=["text", "json"],
        default="text",
        help="Output format. Default: text.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    findings: list[Finding] = []

    if not skill_dir.exists():
        add(findings, "ERROR", "missing-skill-dir", f"Skill directory does not exist: {skill_dir}", path=str(skill_dir))
    elif not skill_dir.is_dir():
        add(findings, "ERROR", "skill-dir-not-directory", f"Skill path is not a directory: {skill_dir}", path=str(skill_dir))

    data: dict[str, Any] | None = None
    body = ""

    if skill_dir.exists() and skill_dir.is_dir():
        data, body = parse_skill_md(skill_dir / "SKILL.md", findings)

    if data is not None:
        validate_name(data, skill_dir, findings)
        validate_description(data, findings)
        validate_optional_fields(data, findings)
        validate_body(body, findings)
        validate_referenced_paths(skill_dir, body, findings)
        validate_scripts(skill_dir, findings)

    if args.output_format == "json":
        for finding in findings:
            msg = f"{finding.level}: {finding.code}: {finding.path}: {finding.message}"
            logging.info(msg)
        print(render_json(findings))
    else:
        print(render_text(findings))

    has_errors = any(item.level == "ERROR" for item in findings)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
