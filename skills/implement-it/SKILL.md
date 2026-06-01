---
name: implement-it
description: Implements existing tasks, issues, stories, or plan items. Use when the user asks to implement, code, build, fix, refactor, finish, or complete a defined task, issue, or story — including tasks referenced by file path (tasks/*.md), by ID (TASK-101, issue #42), by acceptance criteria (AC-1 through AC-4), or as a user story ("code this story: as a user..."). Language and framework agnostic.
compatibility: Designed for Claude Code. Requires bash for script execution. Language and framework agnostic.
metadata:
  domain: software-implementation
  version: "1.0"
---

Implement one or more existing tasks, issues, stories, or plan items using the project's language, framework, architecture, style, and conventions. Satisfy requirements without adding unnecessary complexity or unrelated changes.

## When NOT to use this skill

Do not use implement-it when:

- No defined task, issue, story, or inline acceptance criteria exists — create one first.
- The request is exploratory or acceptance criteria are undefined.
- The user wants a quick prototype without production quality.
- The work is purely architectural review or documentation with no code changes.
- The user is asking how something works, not asking to change it.
- The user is debugging without a task that defines what the fix should do.

## Core workflow

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
16. Write implementation summary: `mkdir -p tasks/implementation`. See [output-rules.md](references/output-rules.md) for naming and structure.
17. If domain terms were defined or clarified, add them to `CONTEXT.md`.

## Before marking complete

- [ ] Every AC-*, FR-*, NFR-*, OBS-* verified against actual code
- [ ] Accessibility checks completed if UI was touched
- [ ] No unrelated files modified
