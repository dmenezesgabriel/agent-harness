---
name: implement-it
description: Implements existing tasks, issues, stories, or plan items using TDD, vertical slices, and existing project conventions. Use when the user asks to implement, code, fix, refactor, or complete a defined task, issue, or story in any language, framework, or layer.
compatibility: Designed for Claude Code. Requires bash for script execution. Language and framework agnostic.
metadata:
  domain: software-implementation
  version: "1.0"
---

Implement one or more existing tasks, issues, stories, or plan items.

This skill is programming-language agnostic.
Use the existing project language, framework, architecture, commands, style, and conventions.

Implementation must satisfy the task requirements without introducing unnecessary complexity, broad rewrites, hidden workarounds, or unrelated changes.

Use design principles selectively — read [design-rules.md](references/design-rules.md) when a design decision arises.

## When NOT to use this skill

Do not use implement-it when:

- There is no defined task, issue, or story with acceptance criteria — create one first.
- The request is exploratory or the acceptance criteria are undefined.
- The user wants a quick one-off answer or a prototype without production quality.
- The work is purely architectural review or documentation with no code changes.
- The user is asking how something works, not asking to change it.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load the project's domain vocabulary. Use this vocabulary consistently in all implementation decisions, test names, and variable names.
2. Read the assigned issue, task, story, plan, or user request. If requirements are ambiguous or contradictory, inspect the codebase first — the answer is often already there. If still unclear after inspection, flag the ambiguity explicitly before coding — do not silently pick an interpretation and implement it. If the user changes scope mid-implementation, stop, clarify the new scope, and assess whether completed work is still valid before continuing.
3. Inspect the codebase before asking questions when the answer can be discovered. See [implementation-rules.md — Codebase exploration](references/implementation-rules.md#codebase-exploration) for what to look for.
4. Identify relevant existing architecture, tests, conventions, components, services, boundaries, accessibility patterns, and ADRs.
5. Implement the smallest safe vertical slice that satisfies the task. See [implementation-rules.md — Vertical-slice implementation](references/implementation-rules.md#vertical-slice-implementation).
6. Use TDD for logic, APIs, services, domain rules, data flows, permissions, and regressions when practical. See [implementation-rules.md — TDD workflow](references/implementation-rules.md#tdd-workflow).
7. Use Component-Driven Development for frontend UI work when practical. See [implementation-rules.md — CDD workflow](references/implementation-rules.md#component-driven-development-workflow).
8. Use semantic HTML and native controls before ARIA for frontend work. Treat accessibility as part of component behavior, not final polish. See [implementation-rules.md — Semantic HTML and accessibility](references/implementation-rules.md#semantic-html-and-accessibility).
9. Apply design principles selectively — read [design-rules.md](references/design-rules.md) when a design decision arises.
10. Preserve architecture boundaries and dependency direction.
11. Add or update only meaningful tests. Every new test must run with the project's single test command (e.g. `pytest`, `npm test`) without manual setup or interactive input. If a test requires infrastructure that is not yet automated, automating it is part of this task — not a follow-up. Read [testing-rules.md](references/testing-rules.md) before adding or changing any test type.
12. Add or update logs, metrics, traces, and analytics only when required by the task. When adding logs, use structured format with named fields (`event=`, `field=`, `value=`), not prose sentences. Applies only to logs modified in this task.
13. Update ADRs when implementation confirms, changes, or rejects architectural assumptions. Read [adr-implementation-rules.md](references/adr-implementation-rules.md) only when touching an ADR-backed decision.
14. Validate with the relevant test, lint, typecheck, build, accessibility, and runtime checks. If validation fails, fix the root cause — do not disable linting, skip tests, or use `--force` flags. If a failure is pre-existing and out of scope, document it in the summary under "Unresolved assumptions". See [implementation-rules.md — Validation loop](references/implementation-rules.md#validation-loop).
15. Re-read the issue and verify every AC-*, FR-*, NFR-*, and OBS-* item against the actual code — not the intended design. For each item, state explicitly whether the code satisfies it. Fix any that do not before writing the summary.
16. Write a short implementation summary. Read [output-rules.md](references/output-rules.md) before writing.
17. If domain terms were defined or clarified during implementation, add them to `CONTEXT.md` at the project root using the format in the existing entries.

## Output files

Create an implementation summary in `tasks/implementation/` when changes are complete.

```bash
mkdir -p tasks/implementation
```

See [output-rules.md](references/output-rules.md) for naming and report structure.

## Before marking complete

- [ ] Every AC-*, FR-*, NFR-*, OBS-* from the issue verified against actual code
- [ ] Accessibility checks completed if any UI was touched
- [ ] No unrelated files modified

## If validation fails

If a validation check (test, lint, build) fails after implementation:
- Fix the root cause, not the check.
- Do not disable linting, skip tests, or use `--force` flags to make CI pass.
- If the failure is pre-existing and out of scope, document it in the summary under "Unresolved assumptions" and do not claim it as a blocker.

## Anti-patterns to avoid

**Scope creep**: Do not rewrite working code unless directly required by the task.

**Pattern-first architecture**: Do not introduce a new architectural pattern mid-task without an ADR. If the pattern is needed, write the ADR first, then implement.

**Frontend-only authorization**: Frontend permission checks are presentation guards, not the source of truth. Backend must enforce every permission — a UI-only check is a security vulnerability.

**Deferred accessibility**: Do not treat accessibility as final polish. After changing interactive UI, forms, modals, or error states, check keyboard navigation, focus behavior, labels, and error announcements before marking the task complete.

**Unjustified "not applicable"**: Do not mark a test type as not applicable unless you have a concrete reason. State the reason in the summary.

**Convention override**: If the codebase uses a different convention than what you would normally choose, follow the codebase convention. Consistency outranks personal preference.

**Unannotated interfaces**: In typed languages (TypeScript, Python, Go, Java, Kotlin, Rust), every new/modified public function, return type, and class field needs an explicit type annotation. Not applicable to untyped languages.

**Generic naming**: Avoid `data`, `handler`, `result`, `item`, `Manager` — use names from the project's domain vocabulary.

**Deep nesting**: Keep new code ≤2–3 nesting levels. Use guard clauses and early returns.

**Vague error messages**: Every exception must include the offending value and expected constraint, not just a label. Example: `ValueError(f"Unknown adapter {name!r}; expected one of {list(registry)}")` not `ValueError("Invalid adapter")`.

**Routine ADR update**: Do not update ADRs for routine changes. Update only when implementation confirms, changes, or rejects an architectural assumption.

## Final response

After implementation, summarize:

- files changed
- behavior implemented
- tests added or updated
- validations run
- accessibility checks run, if relevant
- ADRs updated, if any
- intentional non-applicable test categories
- unresolved assumptions or follow-up work