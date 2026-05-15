---
name: skill-builder
description: Use this skill to create, validate, lint, refactor, or fix Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
compatibility: Requires uv and Python 3.11+ for the bundled validator script.
---
## Purpose

Create, validate, lint, refactor, and fix Agent Skills by generating or editing SKILL.md frontmatter and body, writing support files (scripts, references, assets, evals), and validating against the Agent Skills specification.

## Directory structure

```text
skill-name/
├── SKILL.md          # Required: activation metadata + core instructions
├── scripts/          # Optional: executable helpers
├── references/       # Optional: detailed docs loaded on demand
├── assets/           # Optional: templates, schemas, examples, resources
└── evals/            # Optional: test prompts, fixtures, assertions
```

## Workflow

1. **Clarify the task.** Determine whether the user wants to create a new skill, validate/lint an existing skill, or refactor/improve one.
2. **Inspect the current skill files.** Read `SKILL.md` and any existing support files to understand the current state.
3. **Load reference files on demand.**
   - Read `references/specification.md` when creating or validating structure, frontmatter, naming, or progressive-disclosure rules.
   - Read `references/best-practices.md` when designing workflows, improving instructions, or adding examples and edge cases.
   - Read `references/optimizing-descriptions.md` when writing or refining the activation `description`.
   - Read `references/using-scripts.md` when adding or fixing CLI helpers in `scripts/`.
   - Read `references/evaluating-skills.md` when creating or updating test prompts and assertions in `evals/`.
4. **Create or update `SKILL.md`.** Write accurate frontmatter (`name`, `description`), a clear purpose statement, an ordered workflow, representative examples, and known edge cases.
5. **Create or update support files** only when they reduce context load or improve repeatability — scripts for deterministic checks, references for deep context, assets for templates, evals for test coverage.
6. **Run the bundled validator.** Execute the validation script from the skill root:
   ```bash
   uv run scripts/validate_skill.py --skill-dir .
   ```
   Fix any errors or warnings it reports.
7. **Report results.** Summarise what was created or changed, note any remaining warnings, and suggest next steps (e.g., authoring evals, adding edge-case coverage, or iterating on the description).

## Edge cases

- **Name must match directory.** The `name` field in frontmatter must be identical to the parent directory name. If they differ, the skill won't pass validation.
- **Description controls activation.** The `description` field is what the agent uses to decide whether to load the skill. Don't bury trigger conditions only in the body. The description must be activation-oriented — tell the agent *when* to use the skill, not just *what* it does.
- **Support files must use relative paths.** All references to support files (in scripts/, references/, assets/, evals/) must be relative to the skill root. Absolute paths will fail when the skill is used in a different environment.
- **Every reference needs a load condition.** When referencing a file in references/, always tell the agent *exactly when* to read it. A reference without a condition ("See references/") wastes context because the agent won't know when it's relevant.
- **Scripts must be non-interactive.** Agents run in non-interactive shells. Any script that calls `input()` or blocks on TTY input will hang indefinitely. All input must come from CLI flags, env vars, or stdin.
- **Don't create empty directories.** Empty assets/ or evals/ directories add noise without value. Only create support directories when they contain actual files.
- **PEP 723 for Python script deps.** If a Python script needs external packages, declare them inline with PEP 723 script metadata (`# /// script` + `# dependencies = [...]`). Don't create separate requirements files for script-only dependencies.

## Output format

When you complete a task, report results using the following template:

```markdown
## Summary
<one-sentence result>

## Changes
- <path>: <what changed>

## Validation
<validator output>

## Remaining issues
- <issue or "None">

## Suggested next steps
1. <step>
```

## Evaluation

Run structured evaluations to measure the skill's output quality and iterate on improvements.

### Setup

Create a workspace directory alongside the skill directory:

```text
skill-builder-workspace/
└── iteration-1/
    ├── eval-<id>-<name>/
    │   ├── with_skill/
    │   │   └── run-1/
    │   │       ├── outputs/
    │   │       ├── timing.json
    │   │       └── grading.json
    │   └── without_skill/
    │       └── run-1/
    │           ├── outputs/
    │           ├── timing.json
    │           └── grading.json
    ├── benchmark.json
    └── benchmark.md
```

### Step 1: Spawn eval runs

For each test case in `evals/evals.json`, spawn two parallel subagents in the same turn:

- **With-skill run**: provide the skill path, the eval prompt, input files, and save outputs to `with_skill/outputs/`.
- **Baseline run**: same prompt, no skill path, save to `without_skill/outputs/`.

Write an `eval_metadata.json` in each eval directory:

```json
{"eval_id": "<id>", "eval_name": "<name>", "prompt": "<prompt>", "assertions": [...]}
```

### Step 2: Capture timing

When each subagent completes, save the `total_tokens` and `duration_ms` from the task notification to `timing.json`:

```json
{"total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3}
```

### Step 3: Run deterministic checks

For each run, execute the check script before grading:

```bash
uv run scripts/check_assertions.py --evals-json evals/evals.json --outputs-dir <run>/outputs/ --run-dir <run>
```

This produces `checks.json` with auto-pass/fail for assertions that have executable checks. Only assertions that pass all their checks AND have no remaining subjective criteria need no grader attention.

### Step 4: Grade remaining assertions

For each run, spawn a grader subagent. Pass it only the assertions that were NOT resolved by checks.json. Read `agents/grader.md` for full instructions. The grader writes `grading.json`. After grading, merge checks.json + grading.json into the final grading.json (checks overwrite for their assertions).

### Step 5: Aggregate into benchmark

```bash
uv run scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name skill-builder
```

This reads all grading.json files and produces `benchmark.json` (structured) and `benchmark.md` (human-readable) with mean &plusmn; stddev per configuration and the delta.

### Step 6: Generate review report

```bash
uv run eval-viewer/generate_review.py <workspace>/iteration-N --skill-name skill-builder --static <workspace>/iteration-N/review.html
```

Open the generated `review.html` in a browser to browse runs, see outputs, review assertion grades, and leave feedback.

### Step 7: Iterate

Read `feedback.json`, identify failures, improve the skill, then repeat from Step 1 in a new `iteration-<N+1>/` directory.

## Support files

Reference support files by relative path from the skill root. Load them only when the task requires them.

### References

- Read `references/specification.md` when creating, validating, linting, or fixing skill structure, `SKILL.md` frontmatter, naming rules, optional fields, body requirements, support-file references, or progressive-disclosure rules.
- Read `references/best-practices.md` when improving skill scope, instruction quality, workflow design, gotchas, examples, templates, validation loops, or context efficiency.
- Read `references/optimizing-descriptions.md` when writing or refining the `description` field, improving activation precision, debugging false positives, debugging false negatives, or designing trigger evals.
- Read `references/evaluating-skills.md` when creating eval cases, expected outputs, assertions, grading rules, baseline comparisons, benchmark reports, or iteration loops.
- Read `references/using-scripts.md` when adding, reviewing, or fixing files in `scripts/`, especially CLI interfaces, dependencies, `--help`, errors, structured output, and non-interactive execution.

### Scripts

Use `scripts/` for deterministic validation, linting, formatting, scoring, generation, or repeatable checks.

Run the bundled validator after creating or changing a skill:

```bash
uv run scripts/validate_skill.py --skill-dir .
```

Use JSON output when another script or agent needs machine-readable diagnostics:

```sh
uv run scripts/validate_skill.py --skill-dir . --format json
```

### Assets

Use `assets/` for reusable templates, schemas, examples, fixtures, rubrics, and output formats.

Load assets only when the workflow explicitly requires that template, schema, fixture, or rubric.

## Skill template

A minimal `SKILL.md` template is available at `assets/skill-template.md`.

Load it when creating a new skill from scratch.
