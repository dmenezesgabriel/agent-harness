---
name: plan-it
description: Creates a sequenced implementation plan as self-contained task files with requirements, acceptance criteria, tests, and ADR stubs. Use when the user asks to plan, break down, scope, sequence, or prepare work — or says "plan this", "create tasks", "break this down", or "what's the plan".
compatibility: Designed for Claude Code. Requires bash for script execution and a git repository for project context.
metadata:
  domain: software-planning
  version: "1.0"
---

Create an implementation plan with _one or more tasks_.

Each task must be short, concrete, testable, and self-contained.
Do not create artificial tiny tasks.
Do not create bureaucratic sections with duplicated content.

## When NOT to use this skill

Do not use plan-it when:

- The request is exploratory or vague — the problem must be defined before planning.
- The user wants a quick prototype or spike without formal task structure.
- The work is a single-line bug fix with no dependencies or architectural implications.
- The user is asking a question or reviewing existing work, not requesting a plan.
- An implementation is already underway and only code changes are needed.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load the project's domain vocabulary. Use this vocabulary consistently in all task names, requirements, and acceptance criteria.
2. Identify unresolved decisions, hidden assumptions, and missing constraints. If an assumption cannot be resolved and blocks task sequencing, flag it and pause — do not plan around an unresolved blocker. If scope changes mid-planning, stop and clarify the new scope before continuing. (See [planning-rules.md — Planning clarification rule](references/planning-rules.md#planning-clarification-rule).)
3. Clarify only what cannot be discovered from the codebase. Inspect first; ask only what inspection cannot answer.
4. Prefer tracer-bullet vertical slices over horizontal layer work. (See [planning-rules.md — Tracer-bullet planning](references/planning-rules.md#tracer-bullet-planning).)
5. Keep irreversible architecture decisions open as long as practical. (See [planning-rules.md — Keep decisions open](references/planning-rules.md#keep-decisions-open).)
6. Identify whether any task requires an ADR stub. If yes, read [adr-rules.md](references/adr-rules.md) before writing the stub.
7. Create prioritized tasks with dependencies and enough context to execute. Read [planning-rules.md — Priority and Dependencies](references/planning-rules.md#priority) for priority and dependency guidance.
8. Select test types. Read [test-selection.md](references/test-selection.md) before choosing unit, integration, smoke, E2E, regression, performance, security, usability, or observability tests.
9. Define requirements, acceptance criteria, and observability. If two requirements contradict each other, flag the conflict explicitly in the task under "Unresolved assumptions" — do not silently pick one interpretation. (See [planning-rules.md — Task sections](references/planning-rules.md#task-sections).)
10. Classify each task as **AFK** (can be completed autonomously by an agent without human review) or **HITL** (requires human involvement at a named decision point — state the decision). Read [planning-rules.md — HITL/AFK classification](references/planning-rules.md#hitlafk-classification) for criteria.
11. Write one Markdown issue file per task in `issues/`. Read [output-files.md](references/output-files.md) for naming conventions. Use [assets/task-template.md](assets/task-template.md) as the exact structure.
12. Write ADR stubs in `docs/adrs/` only when architecture decisions are needed. Use [assets/adr-template.md](assets/adr-template.md) as the exact structure.
13. If domain terms were defined or clarified during planning, add them to `CONTEXT.md` at the project root using the format in [assets/context-template.md](assets/context-template.md).

## Issue output requirement

After all tasks are defined, create one Markdown file per task in `issues/`.

Before writing issue files, run:

```bash
bash scripts/ensure-issues-dir.sh issues
```

Then write task files using priority and dependency order:

```text
issues/001-create-project.md
issues/002-invite-project-member.md
issues/003-protect-project-settings.md
```

## ADR output requirement

During planning, identify whether any task needs an Architectural Decision Record.

Create an ADR stub when a task depends on a decision that is hard to reverse, cross-cutting, or affects architecture boundaries, data, infrastructure, security, scalability, protocols, vendors, or external dependencies.

Do not create ADRs for ordinary implementation details.

Before writing ADR files, run:

```bash
bash scripts/ensure-adrs-dir.sh docs/adrs
```

Then write ADR files using chronological numeric order:

```text
docs/adrs/001-use-notification-port.md
docs/adrs/002-store-project-events.md
docs/adrs/003-use-opentelemetry.md
```

## Before marking complete

- [ ] Every issue file in `issues/` has no empty required sections
- [ ] Task numbering reflects dependency order (no task numbered before one it depends on)
- [ ] ADR stubs exist for every task that depends on an architectural decision
- [ ] Each task has an AFK or HITL classification with a named reason
- [ ] `CONTEXT.md` updated if domain terms were defined or clarified

## If output fails

If files cannot be created:
- Verify the setup script ran: `bash scripts/ensure-issues-dir.sh`
- Check directory permissions: `ls -ld issues/`
- Report the error and propose an alternative output location if needed.

## Anti-patterns to avoid

**Artificial task splitting**: Do not create tiny tasks to appear thorough. If the work is atomic, bundle it. A task that blocks nothing and delivers no independent behavior is a horizontal slice pretending to be vertical.

**Cross-section duplication**: Context, Use Cases, and Requirements serve distinct purposes — context explains *why*, use cases describe *who and when*, requirements define *what must be true*. Restating the same fact in all three teaches the reader to skip sections.

**Asking questions the codebase can answer**: Never ask the requester for information available by codebase inspection. Inspect first. Asking questions you could answer yourself is slower and reveals you haven't read the code.

**ADR inflation**: Do not create an ADR for an ordinary implementation detail. ADRs are for decisions that are hard to reverse, cross-cutting, or architecture-level. Routine choices do not need a record.

**Test padding**: Do not mark a test type as applicable unless the task genuinely requires it. Padding the test list wastes implementation effort and devalues the meaningful tests.

**Blocking-unaware ordering**: Task priority order must reflect dependencies. A task that unblocks others must come first, regardless of perceived importance.

## Final response

After creating the files, summarize:

- created issue files
- created ADR files, if any
- task order
- ADR dependencies, if any
- unresolved assumptions, if any
- tests intentionally marked not applicable