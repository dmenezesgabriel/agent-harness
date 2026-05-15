# Agent Skills Specification Reference

Use this reference when creating, validating, linting, fixing, or reviewing an Agent Skill.

A skill is a portable capability package for agents. It must be a directory containing a `SKILL.md` file. Optional support files may live in `scripts/`, `references/`, `assets/`, and `evals/`.

## Required directory shape

```text
skill-name/
├── SKILL.md          # Required: frontmatter + Markdown instructions
├── scripts/          # Optional: executable helpers
├── references/       # Optional: detailed documentation loaded on demand
├── assets/           # Optional: templates, schemas, fixtures, examples
└── evals/            # Optional: eval prompts, fixtures, assertions, benchmarks
```

## Progressive disclosure

Skills are loaded in stages:

1. **Discovery**: the agent reads only `name` and `description`.
2. **Activation**: if the task matches the description, the agent loads the full `SKILL.md`.
3. **Execution**: the agent follows the body and loads support files only when needed.

Keep `SKILL.md` focused. Move detailed or situational material into `references/`, `assets/`, or `scripts/`.

Recommended limits:

- `SKILL.md`: under 500 lines.
- `SKILL.md` body: under 5,000 tokens.
- Description: under 1,024 characters.

## `SKILL.md` format

`SKILL.md` must contain:

1. YAML frontmatter delimited by `---`.
2. Markdown body content after the closing `---`.

Minimal valid shape:

```markdown
---
name: skill-name
description: Use this skill when the user needs a specific capability.
---

## Purpose

Explain the skill scope.

## Workflow

Describe the procedure the agent should follow.
```

## Frontmatter fields

### `name`

Required.

Constraints:

- Must be present.
- Must be a string.
- Must be 1-64 characters.
- Must contain only lowercase letters, numbers, and hyphens.
- Must not start with a hyphen.
- Must not end with a hyphen.
- Must not contain consecutive hyphens.
- Must match the parent directory name.

Valid:

```yaml
name: pdf-processing
name: data-analysis
name: code-review
```

Invalid:

```yaml
name: PDF-Processing   # uppercase not allowed
name: -pdf             # cannot start with hyphen
name: pdf-             # cannot end with hyphen
name: pdf--processing  # consecutive hyphens not allowed
name: pdf_processing   # underscore not allowed
```

### `description`

Required.

Constraints:

- Must be present.
- Must be a string.
- Must be non-empty.
- Must be 1-1024 characters.
- Must describe both:
  - what the skill does;
  - when the agent should use it.
- Should use user-intent keywords that help activation.
- Should be specific enough to avoid false triggers.
- Should be broad enough to catch relevant prompts.

Preferred style:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

Weak style:

```yaml
description: Helps with skills.
```

### `license`

Optional.

Constraints:

- Must be a short string if provided.
- Should name a license or point to a bundled license file.

Examples:

```yaml
license: Apache-2.0
license: MIT
license: Proprietary. See LICENSE.txt.
```

### `compatibility`

Optional.

Use only when the skill has environment requirements.

Constraints:

- Must be a string if provided.
- Must be 1-500 characters.
- Should mention intended agent, system tools, package managers, runtime versions, network needs, or OS assumptions.

Examples:

```yaml
compatibility: Requires Python 3.12+ and uv.
compatibility: Requires git, jq, and internet access.
compatibility: Designed for Claude Code, Codex, or VS Code Copilot agent mode.
```

Do not include `compatibility` when there are no meaningful environment requirements.

### `metadata`

Optional.

Constraints:

- Must be a YAML mapping if provided.
- Keys should be strings.
- Values should be simple scalar values when possible.
- Use reasonably unique key names to avoid client-specific conflicts.

Example:

```yaml
metadata:
  author: example-org
  version: "1.0.0"
  status: stable
```

### `allowed-tools`

Optional and experimental.

Constraints:

- Must be a space-separated string if provided.
- Support varies by agent implementation.
- Use only when the target agent supports it.

Example:

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

## Body content

The Markdown body has no strict format restrictions, but it should be procedural, reusable, and specific.

Recommended sections:

```markdown
## Purpose
<scope, context, and intended outcome>

## When to use
<trigger conditions and boundaries>

## Workflow
<ordered steps the agent should follow>

## Validation
<checks the agent must run before finishing>

## Examples
<input/output examples>

## Edge cases
<constraints, gotchas, and failure corrections>

## Support files
<relative references to scripts, references, assets, and evals>
```

Prefer procedures over declarations.

Good:

```markdown
1. Inspect `SKILL.md`.
2. Validate frontmatter fields.
3. Check relative file references.
4. Run `python scripts/validate_skill.py --skill-dir .`.
5. Fix all reported errors.
```

Weak:

```markdown
Follow best practices.
```

## File references

Reference support files by relative path from the skill root.

Good:

```markdown
Read `references/specification.md` when validating skill structure.
Run `python scripts/validate_skill.py --skill-dir .`.
Use `assets/report-template.md` when generating a report.
```

Avoid:

```markdown
See references for details.
Use the validator script.
```

Rules:

- Use relative paths from the skill root.
- Keep references explicit.
- Tell the agent when to load each referenced file.
- Avoid deeply nested reference chains.
- Do not make `SKILL.md` depend on a reference file without a clear trigger.
- Scripts mentioned in references should still be runnable from the skill root.

## Optional directories

### `scripts/`

Use for deterministic executable helpers.

Scripts should:

- Be non-interactive.
- Accept input through flags, environment variables, files, or stdin.
- Provide `--help`.
- Emit useful errors.
- Use meaningful exit codes.
- Send machine-readable output to stdout.
- Send logs, warnings, and diagnostics to stderr.
- Be idempotent when possible.
- Support `--dry-run` for destructive or stateful operations.
- Avoid unbounded output.
- Prefer explicit flags over guessing.

Simple one-line commands may stay in `SKILL.md` or this reference.

Examples:

```bash
test -f SKILL.md
```

```bash
grep -n '^description:' SKILL.md
```

```bash
python scripts/validate_skill.py --skill-dir .
```

Complex or reusable logic should live in `scripts/`.

### `references/`

Use for detailed documentation loaded only when needed.

Good examples:

```text
references/specification.md
references/best-practices.md
references/optimizing-descriptions.md
references/evaluating-skills.md
references/using-scripts.md
```

Each reference should be focused. Do not duplicate the entire skill body inside references.

### `assets/`

Use for static reusable resources.

Examples:

```text
assets/report-template.md
assets/eval-rubric.json
assets/skill-template.md
assets/frontmatter-schema.yaml
```

Use assets for:

- templates;
- schemas;
- fixtures;
- examples;
- rubrics;
- structured output formats.

### `evals/`

Use for testing skill quality.

Recommended shape:

```text
evals/
├── evals.json
├── files/
└── assertions/
```

`evals/evals.json` should contain realistic prompts, expected outputs, optional input files, and assertions.

Example:

```json
{
  "skill_name": "skill-builder",
  "evals": [
    {
      "id": "valid-minimal-skill",
      "prompt": "Create a minimal skill for validating JSON files.",
      "expected_output": "A valid skill directory with SKILL.md and a precise activation description.",
      "assertions": [
        "SKILL.md exists",
        "frontmatter has valid name",
        "frontmatter has non-empty description",
        "description says what the skill does and when to use it"
      ]
    }
  ]
}
```

## Validation commands

Use these commands from the skill root.

### Check required file

```bash
test -f SKILL.md
```

### Check optional directories

```bash
find . -maxdepth 2 -type d | sort
```

### Check frontmatter delimiter count

```bash
grep -n '^---$' SKILL.md
```

Expected: at least two delimiter lines.

### Check for required fields

```bash
grep -n '^name:' SKILL.md && grep -n '^description:' SKILL.md
```

### Run official/reference validator when available

```bash
skills-ref validate .
```

### Run bundled validator

```bash
python scripts/validate_skill.py --skill-dir .
```

With JSON output:

```bash
python scripts/validate_skill.py --skill-dir . --format json
```

## Bundled validator policy

Use a script when validation requires parsing YAML, checking directory-name equality, scanning references, or producing structured diagnostics.

The validator should check:

- `SKILL.md` exists.
- Frontmatter exists and is closed.
- Frontmatter is valid YAML.
- `name` exists.
- `name` is a string.
- `name` length is 1-64.
- `name` uses only lowercase letters, numbers, and hyphens.
- `name` does not start or end with hyphen.
- `name` does not contain consecutive hyphens.
- `name` matches parent directory name.
- `description` exists.
- `description` is a string.
- `description` length is 1-1024.
- `description` is not empty.
- `compatibility`, if present, is a string of 1-500 characters.
- `metadata`, if present, is a mapping.
- `allowed-tools`, if present, is a string.
- `license`, if present, is a string.
- Markdown body exists.
- Body is not empty.
- Referenced local files exist when written as inline code paths like `references/...`, `scripts/...`, or `assets/...`.
- No obvious absolute local paths are used for bundled files.
- Scripts referenced in Markdown exist.

## Validation result levels

Use these levels:

- `ERROR`: violates the specification or breaks loading.
- `WARNING`: valid but likely weak, brittle, or unclear.
- `INFO`: useful improvement suggestion.

Validation must fail on `ERROR`.

Validation may pass with `WARNING`.

## Common errors

### Missing frontmatter

Invalid:

```markdown
# My Skill

No YAML frontmatter.
```

Fix:

```markdown
---
name: my-skill
description: Use this skill when...
---

# My Skill
```

### Invalid name

Invalid:

```yaml
name: Skill_Builder
```

Fix:

```yaml
name: skill-builder
```

### Weak description

Weak:

```yaml
description: Builds things.
```

Better:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including frontmatter, activation descriptions, instructions, references, scripts, assets, and evals.
```

### Generic support-file reference

Weak:

```markdown
See `references/` for details.
```

Better:

```markdown
Read `references/optimizing-descriptions.md` when improving activation precision, trigger coverage, false positives, or false negatives.
```

## Script authoring rules

For simple commands, use fenced shell snippets directly.

For complex logic, create a script in `scripts/`.

Python scripts should:

- use `argparse`;
- support `--help`;
- use PEP 723 inline dependencies when external packages are required;
- run with `uv run scripts/<name>.py`;
- avoid separate `requirements.txt` for script-only dependencies;
- print JSON to stdout when `--format json` is used;
- print diagnostics to stderr;
- return non-zero exit code on errors.

PEP 723 example:

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

## Final review checklist

Before accepting a skill, verify:

- [ ] Directory name matches `name`.
- [ ] `SKILL.md` exists.
- [ ] Frontmatter is valid YAML.
- [ ] `name` is valid.
- [ ] `description` is precise and activation-oriented.
- [ ] Optional fields follow their constraints.
- [ ] Body contains actionable workflow instructions.
- [ ] Support files are referenced with explicit load conditions.
- [ ] Scripts are non-interactive and documented with `--help`.
- [ ] Complex scripts use `argparse`.
- [ ] Python scripts with dependencies use PEP 723 and `uv run`.
- [ ] Validation command is documented.
- [ ] Evals exist or a reason for omitting them is clear.
