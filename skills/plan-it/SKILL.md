---
name: plan-it
description: Creates a sequenced implementation plan as self-contained task files with requirements, acceptance criteria, tests, and ADR stubs. Use when the user asks to plan, break down, scope, sequence, create tasks, or prepare work — or says "plan this", "create tasks", "break this down", or "what's the plan". Do not use for implementing, coding, building, fixing, completing, refactoring, debugging, reviewing, validating completed work, explaining existing code, or prototype-only requests; implementation verbs must skip even when a task file is mentioned.
compatibility: Designed for Claude Code. Requires bash for script execution and a git repository for project context.
metadata:
  domain: software-planning
  version: "1.0"
---

Create one or more self-contained implementation task files.

Method: enforce exact templates, guide with decision gates, measure before final response.

When planning is requested, create files. A prose-only plan is a failed output. Render each task file with `uv run scripts/render_task.py --input <task.json> --output tasks/issues/NNN-kebab-slug.md`. Every task file path must start with `tasks/issues/`; every ADR file path must start with `docs/adrs/`. Root-level Markdown files are failed output.

## Available Scripts

- `scripts/render_task.py` — renders and validates a task Markdown file from task JSON using the exact task template.

## Required workflow

1. Read `CONTEXT.md` if present; use its vocabulary.
2. Inspect before asking; delegate broad discovery when useful.
3. Ask only sequencing blockers, one numbered question at a time, with one `(recommended)` option.
4. Plan cohesive tracer-bullet tasks; no artificial splits or horizontal-only layers.
5. Keep irreversible decisions open until a task depends on them.
6. Write issue files in `tasks/issues/` by creating task JSON and running the renderer script; do not hand-write task Markdown.
7. Write ADR stubs in `docs/adrs/` only when the ADR gate requires one.
8. Update `CONTEXT.md` only for newly defined or clarified domain terms.
9. Do not write `PLAN_SUMMARY.md` as a substitute for issue files.

## Decision schemas

Use these gates. Do not continue past a failed gate.

```text
planning-readiness:
  reject: vague | prototype | single-line-fix | question | review | implementation-underway
  inspect: any missing fact the repo can answer
  ask: only blockers to sequencing or acceptance criteria
  unavailable_repo_fact: record as assumption, dependency, or prerequisite discovery task; still create issue files
  pass: create task files
```

```text
plan-it-routing:
  invoke: plan | break down | sequence | create tasks | scope implementation | prepare work
  skip: implement | code | build | fix | complete | refactor | debug | review | validate implementation | explain existing code | quick prototype
```

```text
task-shape:
  for each task:
    required: cohesive | concrete | testable | self-contained | system-remains-functional
    order: dependency before priority preference
    dependencies: always include at least one `- ` bullet; use `- No task dependency; ...` only when truly independent
    dependencies: implementation tasks that use prior work must name those prior task IDs or ADR IDs
    assignability: AFK or HITL with specific reason
    HITL: only for the human decision or discovery; do not include blocked implementation requirements in the same task
    sections: no duplicated wording across sections
```

```text
issue-file-contract:
  path: tasks/issues/NNN-kebab-slug.md
  prefix: exactly three digits, starting from the issue counter
  frontmatter: id | created | updated | status=active
  headings: renderer emits assets/task-template.md headings exactly
  forbidden: root-level issue files | PLAN_SUMMARY.md as substitute | alternate sections | four-digit issue prefixes | Pending status
  required_output: at least one task issue file; never create only metadata files such as `.gitignore`
```

```text
renderer-contract:
  command: uv run scripts/render_task.py --input <task.json> --output tasks/issues/NNN-kebab-slug.md
  input: JSON object; no Markdown task hand-writing
  validates: path | frontmatter | headings | bullets | IDs | AFK/HITL | placeholders | required test categories
  on_error: fix the JSON field named in the error and rerun the renderer
```

If `assets/task-template.md` is unavailable, enforce this inline task schema exactly:

```text
task-template-headings:
  frontmatter: id, created, updated, status
  title: "# Task: <clear task name>"
  sections:
    ## Priority
    ## Dependencies
    ## Assignability
    ## Context
    ## Use Cases
    ## Definition of Ready
    ## Functional Requirements
    ## Non-Functional Requirements
    ## Observability Requirements
    ## Acceptance Criteria
    ## Required Tests
    ## Definition of Done
  id-rules:
    IDs must be wrapped in backticks exactly as shown: `FR-001`, `NFR-001`, `OBS-001`, `AC-001`, `UT-001`
    Functional Requirements: at least one backticked `FR-001` entry
    Non-Functional Requirements: at least one backticked `NFR-001` entry or `NFR-001: Not applicable — <specific reason>`
    Observability Requirements: at least one backticked `OBS-001` entry or `OBS-001: Not applicable — <specific reason>`
    Acceptance Criteria: at least one backticked `AC-001` entry
    Required Tests: stable backticked test IDs such as `UT-001`, `IT-001`, or `SMK-001`
  assignability:
    The Assignability section must contain exactly one explicit line shaped `**AFK** — <specific reason>` or `**HITL** — <specific human decision point>`.
    If HITL is needed, create a separate decision/discovery task first, then make implementation tasks depend on it.
    Do not mark implementation tasks HITL because repo facts are unknown; inspect the repo or create a prerequisite discovery task.
  syntax:
    Do not leave angle-bracket placeholders such as `<name>` in generated files.
    If the target language is unknown, describe signatures in prose; do not use language-specific generic syntax with `<...>`.
```

```text
decision-output:
  ADR: create only for hard-to-reverse or architecture-level decisions; link from dependent tasks
  diagram: include only when flow needs >3 bullets or 3+ components interact
  tests: choose by real risk; otherwise mark Not applicable with a specific reason
```

## Lazy references

Load only what the current gate needs:
- [planning-rules.md](references/planning-rules.md): splitting, sequencing, priority, AFK/HITL, clarification.
- [adr-rules.md](references/adr-rules.md): possible ADR.
- [test-selection.md](references/test-selection.md): required tests or not-applicable reasons.
- [diagram-rules.md](references/diagram-rules.md): possible Mermaid diagram.
- [output-files.md](references/output-files.md): file numbering, naming, and ordering before writing.
- [scripts/render_task.py](scripts/render_task.py): required task renderer and JSON contract.
- [assets/task-template.md](assets/task-template.md), [assets/adr-template.md](assets/adr-template.md), [assets/context-template.md](assets/context-template.md): exact schemas.

## Completion checks

- [ ] Every issue file in `tasks/issues/` has no empty required sections
- [ ] Every issue file uses `tasks/issues/NNN-kebab-slug.md` with a three-digit prefix
- [ ] Every issue file uses exact headings and frontmatter from `assets/task-template.md`
- [ ] Task numbering reflects dependency order (no task numbered before one it depends on)
- [ ] ADR stubs exist for every task that depends on an architectural decision
- [ ] Each task has an AFK or HITL classification with a named reason
- [ ] Tests match risk; irrelevant categories say `Not applicable — <specific reason>`
- [ ] `CONTEXT.md` updated if domain terms were defined or clarified

## Final response

After creating files, summarize created issue files, created ADR files, task order, ADR dependencies, unresolved assumptions, and tests intentionally marked not applicable.
