# Agent Skills Best Practices

Use this reference when improving skill scope, instruction quality, workflow design, gotchas, examples, templates, validation loops, or context efficiency.

Do not use this file for strict field constraints. For required structure, frontmatter rules, naming rules, and validation requirements, read `references/specification.md`.

## Core principle

A skill should add knowledge the agent would otherwise miss.

Include:

- domain-specific procedures;
- project-specific conventions;
- fragile sequences;
- non-obvious edge cases;
- preferred tools and defaults;
- validation steps;
- output contracts;
- reusable scripts, templates, schemas, and evals.

Avoid:

- generic advice;
- broad “best practices” without concrete actions;
- long theory sections;
- tool menus without a recommended default;
- instructions that duplicate normal agent behavior;
- rare edge cases in the main `SKILL.md` body.

## Scope

Design each skill as one coherent capability.

Good scope:

```text
Create, validate, lint, and improve Agent Skills.
```

Too narrow:

```text
Only check if the name field exists.
```

Too broad:

```text
Improve all agent behavior, prompts, workflows, tools, code quality, and documentation.
```

A good skill should have:

- one clear purpose;
- one primary workflow;
- clear activation boundaries;
- clear exclusions;
- support files for deeper details.

## Description quality

The `description` field is the activation contract. It should tell the agent when to load the skill.

Use this pattern:

```yaml
description: Use this skill when <user-intent>, including <specific task types>, <artifacts>, and <nearby terms>.
```

Good:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

Weak:

```yaml
description: Helps with skills.
```

Rules:

- Start with “Use this skill when...”
- Describe user intent, not internal implementation.
- Include important keywords and artifacts.
- Include nearby task verbs.
- Avoid being so broad that the skill activates for unrelated work.
- Avoid being so narrow that relevant prompts fail to activate.

For deeper description tuning, read `references/optimizing-descriptions.md`.

## Progressive disclosure

Use progressive disclosure to protect context.

Keep in `SKILL.md`:

- purpose;
- activation boundaries;
- default workflow;
- critical gotchas;
- validation checklist;
- explicit references to support files.

Move to `references/`:

- detailed rules;
- long explanations;
- optional variants;
- deep examples;
- extended troubleshooting;
- implementation notes.

Move to `assets/`:

- templates;
- schemas;
- rubrics;
- fixtures;
- reusable examples;
- output formats.

Move to `scripts/`:

- deterministic validation;
- linting;
- scoring;
- formatting;
- generation;
- repeatable checks.

Bad:

```markdown
See `references/` for more details.
```

Good:

```markdown
Read `references/optimizing-descriptions.md` when improving activation precision, debugging false positives, debugging false negatives, or designing trigger evals.
```

## Instruction style

Write instructions as actions.

Prefer:

```markdown
1. Inspect `SKILL.md`.
2. Validate frontmatter.
3. Check support-file references.
4. Run `uv run scripts/validate_skill.py --skill-dir .`.
5. Fix all errors before finalizing.
```

Avoid:

```markdown
Make sure the skill is good and follows best practices.
```

Use:

- imperative verbs;
- ordered steps;
- clear defaults;
- validation gates;
- observable outputs;
- explicit file paths;
- explicit commands.

Avoid:

- vague quality words;
- abstract principles without procedure;
- excessive alternatives;
- unsupported assumptions;
- hidden dependencies.

## Defaults over menus

When multiple valid approaches exist, choose one default.

Good:

```markdown
Use `uv run scripts/validate_skill.py --skill-dir .` for validation.

Use `--format json` when another script or agent needs machine-readable diagnostics.
```

Weak:

```markdown
You can validate with Python, Bash, jq, grep, a custom script, or another tool.
```

Alternatives are allowed, but keep them secondary:

```markdown
Use the bundled validator by default. If Python or uv is unavailable, fall back to the simple shell checks in `references/specification.md`.
```

## Procedures over declarations

A skill should encode a reusable method, not a one-off answer.

Weak:

```markdown
A good skill should be concise and useful.
```

Better:

```markdown
When improving a skill:

1. Identify the task the skill should handle.
2. Rewrite the description as an activation contract.
3. Keep the default workflow in `SKILL.md`.
4. Move detailed rules to `references/`.
5. Add or update eval cases for the changed behavior.
6. Run the validator.
```

## Recommended `SKILL.md` sections

Use this structure unless the skill has a strong reason to differ:

```markdown
## Purpose

<what capability this skill gives the agent>

## When to use

<trigger conditions and boundaries>

## Workflow

<ordered steps>

## Validation

<checks to run before finishing>

## Support files

<relative paths with explicit load conditions>

## Edge cases

<critical gotchas and corrections>
```

Optional sections:

```markdown
## Inputs

<expected inputs, files, arguments, or context>

## Outputs

<required output format or produced files>

## Examples

<representative input/output examples>

## Failure handling

<what to do when validation, scripts, or assumptions fail>
```

## Workflow design

A good workflow is:

- ordered;
- short;
- deterministic where possible;
- specific about files and commands;
- explicit about validation;
- safe to repeat;
- clear about stopping conditions.

Template:

```markdown
## Workflow

1. Clarify the target task and skill scope from the user request.
2. Inspect the current skill files.
3. Validate `SKILL.md` structure and frontmatter.
4. Improve the activation description if needed.
5. Improve the body workflow, examples, edge cases, and support-file references.
6. Add or update support files only when they reduce context load or improve repeatability.
7. Run validation.
8. Report changes, remaining warnings, and next recommended evals.
```

## Validation loops

Every skill should tell the agent how to check its work.

Use this pattern:

```markdown
## Validation

Before finalizing:

1. Run `uv run scripts/validate_skill.py --skill-dir .`.
2. Fix all `ERROR` findings.
3. Review `WARNING` findings and either fix them or explain why they are acceptable.
4. Confirm support-file references use relative paths.
5. Confirm every referenced file has a clear load condition.
```

For skills without scripts, use simple checks:

```bash
test -f SKILL.md
```

```bash
grep -n '^---$' SKILL.md
```

```bash
grep -n '^name:' SKILL.md && grep -n '^description:' SKILL.md
```

## Gotchas

Use gotchas for non-obvious corrections the agent is likely to miss.

Good gotcha:

```markdown
- The `description` field controls activation. Do not bury trigger conditions only in the body.
```

Weak gotcha:

```markdown
- Be careful.
```

Good gotchas are:

- concrete;
- task-specific;
- corrective;
- likely to prevent real errors;
- short enough to keep in `SKILL.md` if critical.

Move long gotcha explanations to references.

## Examples

Examples should show the pattern the agent should imitate.

Good examples include:

- realistic input;
- expected output;
- file paths;
- constraints;
- edge cases.

Weak examples are too generic:

```markdown
Input: create a skill
Output: skill created
```

Better:

```markdown
Input: Create a skill that validates Python project structure.
Output: A `python-project-validator/` directory with `SKILL.md`, `scripts/validate_project.py`, and explicit validation commands.
```

## Templates

Use templates when output format matters.

Good:

```markdown
## Output format

Return:

1. Summary of changes.
2. Files changed.
3. Validation results.
4. Remaining warnings.
5. Suggested eval cases.
```

Better for strict output:

```markdown
## Output format

```text
Summary:
- <one-sentence result>

Files changed:
- <path>: <change>

Validation:
- <command>: <pass/fail>

Remaining issues:
- <issue or "none">
```
```

Store longer templates in `assets/`.

Example:

```markdown
Use `assets/skill-template.md` when creating a new skill from scratch.
```

## Scripts

Use scripts when a task must be repeatable or mechanically checked.

Good script tasks:

- parse YAML frontmatter;
- validate naming rules;
- check support-file references;
- score eval results;
- format generated reports;
- compare two skill versions.

Scripts must be:

- non-interactive;
- runnable from the skill root;
- documented with `--help`;
- explicit about inputs and outputs;
- clear on errors;
- safe by default.

For complex Python scripts:

- use `argparse`;
- use PEP 723 inline dependencies if external packages are needed;
- run with `uv run`;
- avoid separate requirements files for script-only dependencies.

Example command:

```bash
uv run scripts/validate_skill.py --skill-dir .
```

Machine-readable output:

```bash
uv run scripts/validate_skill.py --skill-dir . --format json
```

For deeper script rules, read `references/using-scripts.md`.

## Assets

Use assets for reusable material that should not clutter `SKILL.md`.

Good assets:

```text
assets/skill-template.md
assets/eval-template.json
assets/output-rubric.md
assets/frontmatter-examples.yaml
```

Reference assets with conditions:

```markdown
Use `assets/skill-template.md` when creating a new skill from scratch.
Use `assets/eval-template.json` when adding the first eval file.
```

Avoid:

```markdown
Check assets if useful.
```

## References

Use references for detail that is important but not always needed.

Good references:

```text
references/specification.md
references/best-practices.md
references/optimizing-descriptions.md
references/evaluating-skills.md
references/using-scripts.md
```

Each reference should have:

- one clear purpose;
- clear trigger conditions from `SKILL.md`;
- no unnecessary duplication;
- explicit commands when relevant;
- examples that support the workflow.

## Evals

Use evals to verify that the skill improves outcomes.

Add evals when:

- creating a new skill;
- changing the activation description;
- changing the workflow;
- adding scripts;
- fixing repeated failures;
- comparing two versions.

A useful eval includes:

- realistic prompt;
- expected output;
- optional input files;
- objective assertions;
- with-skill vs baseline comparison when possible.

Example:

```json
{
  "id": "fix-weak-description",
  "prompt": "Improve this skill description so it triggers correctly but not too broadly.",
  "expected_output": "A revised activation-oriented description with clear scope and near-miss boundaries.",
  "assertions": [
    "Description starts with activation-oriented phrasing",
    "Description says what the skill does",
    "Description says when to use it",
    "Description is under 1024 characters"
  ]
}
```

For deeper eval design, read `references/evaluating-skills.md`.

## Common failure modes

### The skill is too generic

Symptom:

```markdown
description: Helps with development.
```

Fix:

```markdown
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

### The skill body is too long

Symptom:

- many rare edge cases in `SKILL.md`;
- long theory sections;
- duplicated reference content.

Fix:

- keep core workflow in `SKILL.md`;
- move detailed rules to `references/`;
- add explicit load conditions.

### The workflow is vague

Symptom:

```markdown
Review the skill and improve it.
```

Fix:

```markdown
1. Validate frontmatter.
2. Check activation description.
3. Review workflow steps.
4. Check support-file references.
5. Run validation.
6. Fix errors.
```

### The skill hides critical instructions in references

Symptom:

- `SKILL.md` does not mention when to load support files;
- important gotchas only appear in references.

Fix:

- keep critical gotchas in `SKILL.md`;
- reference files with explicit triggers.

### The script is hard for agents to run

Symptom:

- no `--help`;
- interactive prompts;
- unclear required arguments;
- output only in prose;
- no exit codes.

Fix:

- use `argparse`;
- require explicit flags;
- print helpful errors;
- support JSON output;
- exit non-zero on failure.

## Skill quality checklist

Before finalizing a skill, check:

- [ ] The skill has one coherent capability.
- [ ] The description is activation-oriented.
- [ ] The description includes what the skill does and when to use it.
- [ ] The body contains a clear workflow.
- [ ] The workflow is ordered and actionable.
- [ ] Defaults are explicit.
- [ ] Alternatives are limited.
- [ ] Critical gotchas are visible in `SKILL.md`.
- [ ] Long details are moved to `references/`.
- [ ] Templates, schemas, rubrics, and fixtures are in `assets/`.
- [ ] Deterministic checks are in `scripts/`.
- [ ] Scripts are non-interactive and expose `--help`.
- [ ] Support files are referenced by relative path.
- [ ] Every support-file reference has a load condition.
- [ ] Validation commands are documented.
- [ ] Evals exist for important behavior, or a reason for omission is clear.
