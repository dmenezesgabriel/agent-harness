# Using Scripts in Agent Skills

Use this reference when adding, reviewing, or fixing files in `scripts/`, especially CLI interfaces, dependencies, `--help`, errors, structured output, non-interactive execution, and repeatable validation.

Do not use this file for strict skill field constraints. For `SKILL.md` structure, frontmatter rules, naming rules, and support-file references, read `references/specification.md`.

Do not use this file for general skill quality. For scope, workflow design, gotchas, examples, and validation loops, read `references/best-practices.md`.

## Core principle

Use scripts when a task should be deterministic, repeatable, inspectable, or easier to execute than describe.

Good script use cases:

- validate `SKILL.md` frontmatter;
- lint skill directory structure;
- check referenced files exist;
- score eval results;
- format generated reports;
- transform structured data;
- compare two skill versions;
- run mechanical assertions;
- generate templates from parameters.

Avoid scripts for:

- simple prose judgment;
- one-off instructions that are easier in Markdown;
- tasks requiring interactive prompts;
- tasks where agent reasoning is more useful than automation;
- fragile commands with hidden environment assumptions.

## Script directory

Place reusable executable helpers in:

```text
scripts/
├── validate_skill.py
├── grade_eval.py
└── render_template.py
```

Reference scripts from `SKILL.md` by relative path from the skill root:

```markdown
Run `uv run scripts/validate_skill.py --skill-dir .` after creating or changing a skill.
```

Avoid vague references:

```markdown
Use the scripts if needed.
```

Prefer explicit triggers:

```markdown
Run `uv run scripts/grade_eval.py --eval-dir <path> --format json` when grading eval output mechanically.
```

## When to use inline shell snippets

Use one-line shell snippets directly in `SKILL.md` or references when the command is simple and self-explanatory.

Examples:

```bash
test -f SKILL.md
```

```bash
grep -n '^---$' SKILL.md
```

```bash
grep -n '^name:' SKILL.md && grep -n '^description:' SKILL.md
```

```bash
find . -maxdepth 2 -type f | sort
```

Move logic into `scripts/` when the command:

- has multiple branches;
- parses YAML, JSON, Markdown, or files;
- needs reusable error handling;
- needs structured output;
- will be run repeatedly;
- is hard to read as one shell line;
- needs tests or dependencies.

## Script requirements

Every script should be:

- non-interactive;
- runnable from the skill root;
- documented with `--help`;
- explicit about required inputs;
- deterministic when possible;
- safe by default;
- clear on failure;
- idempotent when possible;
- compatible with automation;
- easy for an agent to call.

Scripts must not require:

- TTY prompts;
- passwords entered interactively;
- confirmation menus;
- hidden local state;
- manual setup not documented in `compatibility` or the script help.

Bad:

```python
name = input("Skill name: ")
```

Good:

```bash
uv run scripts/create_skill.py --name json-validator --output-dir .
```

## CLI design

Use flags instead of positional guessing.

Preferred shape:

```bash
uv run scripts/validate_skill.py --skill-dir . --format json
```

Good flags:

```text
--skill-dir
--input
--output
--format
--dry-run
--strict
--verbose
--quiet
```

Use positional arguments only when the script has one obvious input.

Good:

```bash
python scripts/count_lines.py SKILL.md
```

Better for reusable skill scripts:

```bash
uv run scripts/count_lines.py --path SKILL.md --format json
```

## `--help`

Every non-trivial script must support `--help`.

The help output should include:

- one-sentence purpose;
- required arguments;
- optional arguments;
- defaults;
- examples;
- output behavior;
- exit code behavior when useful.

Example:

```text
Validate an Agent Skill directory.

Examples:
  uv run scripts/validate_skill.py --skill-dir .
  uv run scripts/validate_skill.py --skill-dir . --format json
```

## Python script standard

For Python scripts:

- use `argparse`;
- use `pathlib.Path`;
- use type hints;
- use clear functions;
- keep `main()` small;
- return meaningful exit codes;
- write diagnostics to stderr;
- write primary output to stdout;
- support `--format json` for machine-readable output when useful;
- use PEP 723 inline dependencies when external packages are needed;
- run with `uv run`.

Do not create a separate `requirements.txt` only for skill scripts when PEP 723 is sufficient.

## PEP 723 with `uv run`

Use PEP 723 inline metadata for Python scripts with external dependencies.

Template:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
# ///
```

Run:

```bash
uv run scripts/validate_skill.py --skill-dir .
```

With JSON output:

```bash
uv run scripts/validate_skill.py --skill-dir . --format json
```

Use exact or bounded versions for reproducibility:

```python
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
```

Avoid unbounded dependency declarations for important scripts:

```python
# dependencies = [
#   "pyyaml",
# ]
```

## Python `argparse` template

Use this template for complex Python scripts:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Describe what this script does.",
        epilog=(
            "Examples:\n"
            "  uv run scripts/example.py --input input.txt --format json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input file path.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format. Default: text.",
    )
    return parser


def run(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    return {
        "ok": True,
        "input": str(input_path),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = run(args.input)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("PASS" if result["ok"] else "FAIL")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Output contract

Design output so the agent can reliably interpret it.

Use stdout for primary results.

Use stderr for:

- warnings;
- errors;
- progress logs;
- diagnostics;
- debug details.

Good stdout JSON:

```json
{
  "ok": false,
  "summary": {
    "errors": 2,
    "warnings": 1
  },
  "findings": [
    {
      "level": "ERROR",
      "code": "missing-description",
      "path": "SKILL.md",
      "message": "Required frontmatter field `description` is missing."
    }
  ]
}
```

Good text output:

```text
ERROR: missing-description: SKILL.md: Required frontmatter field `description` is missing.
WARNING: description-too-short: SKILL.md: Description may be too vague.
```

Avoid ambiguous output:

```text
Looks mostly fine.
```

## Exit codes

Use predictable exit codes:

```text
0  success
1  validation errors, failed checks, or invalid input
2  command-line usage error when not handled by argparse
```

For validators:

- return `0` when there are no `ERROR` findings;
- return `1` when there is at least one `ERROR`;
- allow `WARNING` findings without failing unless `--strict` is set.

Example behavior:

```bash
uv run scripts/validate_skill.py --skill-dir .
echo $?
```

## JSON output

Support `--format json` when output may be consumed by another script, test, or agent.

Recommended shape:

```json
{
  "ok": true,
  "summary": {
    "errors": 0,
    "warnings": 1,
    "infos": 2,
    "total": 3
  },
  "findings": [
    {
      "level": "WARNING",
      "code": "description-too-short",
      "path": "SKILL.md",
      "message": "Description may be too vague."
    }
  ]
}
```

Use stable keys:

```text
ok
summary
findings
level
code
path
message
```

Do not print logs to stdout when `--format json` is used. Logs should go to stderr.

## Error messages

Good errors are specific and actionable.

Weak:

```text
Invalid file.
```

Better:

```text
ERROR: SKILL.md is missing required frontmatter field `description`.
```

Best:

```text
ERROR: missing-description: SKILL.md: Required frontmatter field `description` is missing. Add `description: Use this skill when...` to the YAML frontmatter.
```

Include:

- what failed;
- where it failed;
- why it failed;
- how to fix it when simple.

## Safety and idempotency

Scripts should be safe by default.

For scripts that modify files:

- support `--dry-run`;
- print changed paths;
- avoid deleting files unless explicitly requested;
- create parent directories only when needed;
- avoid overwriting files unless `--force` is passed;
- write temporary files atomically when practical.

Example:

```bash
uv run scripts/render_template.py \
  --template assets/skill-template.md \
  --output SKILL.md \
  --dry-run
```

Use `--force` for overwrites:

```bash
uv run scripts/render_template.py \
  --template assets/skill-template.md \
  --output SKILL.md \
  --force
```

## Dependency policy

Prefer standard library for simple scripts.

Use external dependencies only when they materially improve correctness or simplicity.

Good external dependency use:

- `pyyaml` for YAML frontmatter parsing;
- `jsonschema` for schema validation;
- `rich` only if human-readable terminal output is important;
- `typer` only if the CLI is large enough to justify it.

For most skill scripts, prefer `argparse` over heavier CLI frameworks.

Pin or bound versions:

```python
# dependencies = [
#   "pyyaml>=6.0.2,<7",
#   "jsonschema>=4.23,<5",
# ]
```

## One-off package commands

Use one-off package commands when an existing tool already does the job.

Examples:

```bash
uvx ruff@0.8.0 check .
```

```bash
npx eslint@9 --fix .
```

```bash
go run golang.org/x/tools/cmd/goimports@v0.28.0 .
```

Rules:

- pin versions when reproducibility matters;
- document prerequisites;
- prefer `uvx` for Python tools when `uv` is available;
- prefer `npx` only when Node.js/npm is assumed;
- move complex command sequences into scripts.

## Shell scripts

Use shell scripts for simple orchestration.

Shell scripts should:

- start with a shebang;
- use strict mode;
- validate arguments;
- quote variables;
- print clear errors;
- avoid interactive prompts.

Template:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scripts/check_required_files.sh <skill-dir>" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

skill_dir="$1"

if [[ ! -f "$skill_dir/SKILL.md" ]]; then
  echo "ERROR: missing SKILL.md in $skill_dir" >&2
  exit 1
fi

echo "PASS: SKILL.md exists"
```

Run:

```bash
bash scripts/check_required_files.sh .
```

Use Python instead of shell when logic requires parsing, nested conditions, JSON, YAML, or cross-platform behavior.

## Script examples for skill-builder

### Validate skill

```bash
uv run scripts/validate_skill.py --skill-dir .
```

JSON:

```bash
uv run scripts/validate_skill.py --skill-dir . --format json
```

Strict mode if supported:

```bash
uv run scripts/validate_skill.py --skill-dir . --strict
```

### Grade eval output

```bash
uv run scripts/grade_eval.py \
  --outputs .workspaces/skill-builder/iteration-1/create-minimal-skill/with_skill/outputs \
  --assertions evals/assertions/create-minimal-skill.json \
  --format json
```

### Render template

```bash
uv run scripts/render_template.py \
  --template assets/skill-template.md \
  --output ./new-skill/SKILL.md \
  --var name=json-validator \
  --var description="Use this skill when validating JSON files."
```

## Referencing scripts from `SKILL.md`

Add script references with explicit conditions.

Good:

```markdown
Run `uv run scripts/validate_skill.py --skill-dir .` after creating or changing any skill file.
```

Good:

```markdown
Run `uv run scripts/grade_eval.py --eval-dir <path> --format json` when grading eval outputs mechanically.
```

Weak:

```markdown
There are scripts in `scripts/`.
```

Good support-file section:

```markdown
## Scripts

- Run `uv run scripts/validate_skill.py --skill-dir .` after creating or changing a skill.
- Run `uv run scripts/validate_skill.py --skill-dir . --format json` when machine-readable diagnostics are needed.
- Run `uv run scripts/grade_eval.py --eval-dir <path> --format json` when grading eval artifacts.
```

## Testing scripts

At minimum, test:

```bash
uv run scripts/validate_skill.py --help
```

```bash
uv run scripts/validate_skill.py --skill-dir .
```

```bash
uv run scripts/validate_skill.py --skill-dir . --format json
```

For scripts with failure behavior, test invalid input:

```bash
uv run scripts/validate_skill.py --skill-dir ./missing-dir
```

Expected:

- clear error message;
- non-zero exit code;
- no traceback for normal user mistakes;
- valid JSON when `--format json` is requested, if possible.

## Common failure modes

### Interactive script

Bad:

```python
confirm = input("Overwrite file? ")
```

Fix:

```bash
uv run scripts/render_template.py --output SKILL.md --force
```

### Hidden dependency

Bad:

```python
import yaml
```

with no dependency declaration.

Fix:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
# ///
```

### No help output

Bad:

```python
sys.argv[1]
```

Fix:

```python
parser = argparse.ArgumentParser(description="Validate an Agent Skill directory.")
```

### Ambiguous stdout

Bad:

```text
Done.
```

Fix:

```json
{
  "ok": true,
  "summary": {
    "errors": 0,
    "warnings": 0
  }
}
```

### Logs mixed with JSON

Bad stdout:

```text
Checking files...
{"ok": true}
```

Fix:

```text
stderr: Checking files...
stdout: {"ok": true}
```

### Script modifies files without preview

Bad:

```bash
python scripts/fix.py
```

Fix:

```bash
uv run scripts/fix.py --skill-dir . --dry-run
uv run scripts/fix.py --skill-dir . --apply
```

## Script review checklist

Before accepting a script, verify:

- [ ] It is in `scripts/`.
- [ ] It is referenced from `SKILL.md` or a relevant reference file.
- [ ] The reference explains when to run it.
- [ ] It is non-interactive.
- [ ] It supports `--help`.
- [ ] It uses explicit arguments.
- [ ] Python scripts use `argparse`.
- [ ] Python scripts use PEP 723 metadata when external dependencies are needed.
- [ ] It can run with `uv run` if Python.
- [ ] It sends primary output to stdout.
- [ ] It sends diagnostics to stderr.
- [ ] It uses meaningful exit codes.
- [ ] It gives actionable errors.
- [ ] It supports JSON output when useful.
- [ ] It avoids destructive behavior by default.
- [ ] It supports `--dry-run` or `--force` when modifying files.
- [ ] It has been tested with `--help`.
- [ ] It has been tested on valid input.
- [ ] It has been tested on invalid input.

## Final rule

Use scripts to make agent behavior more reliable, not more complex.

A script is worth adding when it prevents repeated mistakes, validates something mechanically, or makes a fragile workflow safer and easier to execute.