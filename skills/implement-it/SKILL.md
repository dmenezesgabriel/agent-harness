---
name: implement-it
description: Implements existing tasks, issues, stories, or plan items. Use when the user asks to implement, code, build, fix, refactor, finish, complete, or finish a defined task, issue, or story — including tasks referenced by file path (tasks/*.md), by ID (TASK-101, issue #42), by acceptance criteria (AC-1 through AC-4), or as a user story ("code this story: as a user..."). Language and framework agnostic.
compatibility: Designed for Claude Code. Requires bash for script execution and a git repository for project context.
metadata:
  domain: software-implementation
  version: "2.0"
---

Implement one or more existing tasks, issues, stories, or plan items. Satisfy requirements without adding unnecessary complexity or unrelated changes.

Method: enforce exact summary template, guide with decision gates, measure before final response.

When implementation is requested, code and summarize. An implementation with no summary file is a failed output. Render each summary with `uv run scripts/render_implementation.py --input <summary.json> --output tasks/implementation/NNN-kebab-slug-summary.md`. Every summary file path must start with `tasks/implementation/`. Root-level Markdown files are failed output.

## When NOT to use this skill

Do not use implement-it when:

- No defined task, issue, story, or inline acceptance criteria exists — create one first.
- The request is exploratory or acceptance criteria are undefined.
- The user wants a quick prototype without production quality.
- The work is purely architectural review or documentation with no code changes.
- The user is asking how something works, not asking to change it.
- The user is debugging without a task that defines what the fix should do.

## Available Scripts

| Script | When to run | Output |
|--------|-------------|--------|
| `scripts/ensure-implementation-dir.sh` | First, before writing any summary files | Creates `tasks/implementation/` |
| `scripts/render_implementation.py --input... --output...` | Once per implementation, after writing the JSON | Validated summary Markdown |

All scripts support `--help` / `-h` for full usage details.

## Required workflow

1. If `CONTEXT.md` exists at the project root, read it for domain vocabulary. Use it consistently in all implementation decisions, test names, and variable names.
2. Read the assigned task. If requirements are ambiguous, inspect the codebase first — the answer is often already there. If still unclear after inspection, flag ambiguity explicitly before coding. If scope changes mid-implementation, stop, clarify, and assess whether completed work is still valid.
3. Inspect the codebase before asking questions. See [implementation-rules.md — Codebase exploration](references/implementation-rules.md#codebase-exploration).
4. Identify relevant architecture, tests, conventions, components, services, boundaries, and ADRs.
5. Implement the smallest safe vertical slice. See [implementation-rules.md — Vertical-slice implementation](references/implementation-rules.md#vertical-slice-implementation).
6. Use TDD for logic, APIs, services, domain rules, data flows, permissions, and regressions. See [implementation-rules.md — TDD workflow](references/implementation-rules.md#tdd-workflow).
7. For frontend UI work, use CDD. See [implementation-rules.md — CDD workflow](references/implementation-rules.md#component-driven-development-workflow).
8. Use semantic HTML and native controls before ARIA. Treat accessibility as component behavior, not final polish.
9. Apply design principles selectively — read [design-rules.md](references/design-rules.md) when a design decision arises. For named patterns, see [design-patterns.md](references/design-patterns.md). For domain classes and Value Objects, see [oop-calisthenics.md](references/oop-calisthenics.md).
10. Preserve architecture boundaries and dependency direction.
11. Add or update only meaningful tests. Every new test must run with the project's single test command without manual setup. Automating required infrastructure is part of this task. Read [testing-rules.md](references/testing-rules.md) before adding or changing any test type.
12. Add or update logs, metrics, traces, and analytics only when required by the task. Use structured format: `event=`, `field=`, `value=`.
13. Update ADRs when implementation confirms, changes, or rejects architectural assumptions. Read [adr-implementation-rules.md](references/adr-implementation-rules.md) only when touching an ADR-backed decision.
14. Validate with relevant tests, lint, typecheck, build, and runtime checks. Fix root causes — do not disable linting, skip tests, or use `--force`. Pre-existing failures out of scope go under "Unresolved assumptions". See [implementation-rules.md — Validation loop](references/implementation-rules.md#validation-loop).
15. Re-read the issue and verify every AC-*, FR-*, NFR-*, and OBS-* item against actual code — not intended design. For each item, state explicitly whether the code satisfies it. Fix any that don't before writing the summary.
16. Write a small JSON input file, then run `uv run scripts/render_implementation.py --input <summary.json> --output tasks/implementation/NNN-kebab-slug-summary.md`; do not hand-write summary Markdown.
17. If domain terms were defined or clarified, add them to `CONTEXT.md`.

## Decision schemas

Use these gates. Do not continue past a failed gate.

```text
implement-it-routing:
  invoke: implement | code | build | fix | refactor | complete | finish
          when backed by a defined task, issue, story, or acceptance criteria
  skip: plan | explore | review | explain | debug | prototype
        without a defined task or acceptance criteria
```

```text
implement-it-readiness:
  reject: no_defined_task | vague_scope | missing_acceptance_criteria
  inspect: existing tests, domain models, components, ADRs, conventions
  ask: only blockers the repo cannot answer; one question, numbered, (recommended)
  pass: implement smallest vertical slice
```

```text
implementation-scope:
  for each implementation:
    required: only what the task requires | smallest vertical slice
    tdd: logic/APIs/services/domain rules
    cdd: frontend UI
    integrity: system remains functional after every change
    boundaries: preserve architecture, no unrelated rewrites
    tests: meaningful, risk-scoped, use lightest test double
    verify: run lint, typecheck, build after each change
```

```text
summary-contract:
  path: tasks/implementation/NNN-kebab-slug-summary.md
  frontmatter: id | issue | created | updated
  sections: Related Task | Files Changed | Behavior Implemented | Design Notes
            | Tests Added or Updated | Test Categories Not Applicable
            | Validation Run | Accessibility Notes | Observability Changes
            | ADR Updates | Unresolved Assumptions or Follow-Up
  forbidden: root-level files | missing frontmatter | placeholder content
```

```text
renderer-contract:
  command: uv run scripts/render_implementation.py --input <summary.json>
           --output tasks/implementation/NNN-kebab-slug-summary.md
  sequence: write JSON -> run renderer -> inspect renderer error if any
            -> fix JSON -> rerun renderer
  input: JSON object; no Markdown summary hand-writing
  validates: path | frontmatter | sections | placeholders | date format
  on_error: fix the JSON field named in the error and rerun the renderer
```

## Lazy references

Load only what the current gate needs:
- [implementation-rules.md](references/implementation-rules.md): codebase exploration, vertical slicing, TDD, CDD, validation loop.
- [design-rules.md](references/design-rules.md): design decisions and principles.
- [design-patterns.md](references/design-patterns.md): named pattern references.
- [oop-calisthenics.md](references/oop-calisthenics.md): Value Objects and domain modeling.
- [testing-rules.md](references/testing-rules.md): test selection and type decisions.
- [output-rules.md](references/output-rules.md): summary naming and structure.
- [adr-implementation-rules.md](references/adr-implementation-rules.md): ADR updates for implementation.
- [scripts/render_implementation.py](scripts/render_implementation.py): required summary renderer and JSON contract.
- [assets/implementation-summary-template.md](assets/implementation-summary-template.md): exact summary schema.
- [assets/implementation-checklist.md](assets/implementation-checklist.md): before/during/validation checks.

## Completion checks

- [ ] Every AC-*, FR-*, NFR-*, OBS-* verified against actual code
- [ ] Accessibility checks completed if UI was touched
- [ ] No unrelated files modified
- [ ] Summary file written to `tasks/implementation/NNN-kebab-slug-summary.md`
- [ ] Summary frontmatter has `id`, `issue`, `created`, `updated`
- [ ] Summary has all 12 required sections
- [ ] Summary validation run is not empty
- [ ] `CONTEXT.md` updated if domain terms were defined or clarified

## Final response

After implementing and writing the summary, summarize: task or issue implemented, files changed, tests added or updated, validation commands run, design decisions made, ADRs updated if any, acceptance criteria status, and unresolved assumptions.
