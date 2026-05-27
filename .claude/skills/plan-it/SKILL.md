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
2. Identify unresolved decisions, hidden assumptions, and missing constraints. If an assumption blocks sequencing, ask one question at a time with numbered alternatives (one marked `recommended`) until resolved — inspect the codebase before asking, delegating exploration to a sub-agent if needed. If scope changes mid-planning, stop and clarify before continuing. See [planning-rules.md — Planning clarification rule](references/planning-rules.md#planning-clarification-rule) for the full decision tree.
3. Clarify only what cannot be discovered from the codebase. Inspect first; ask only what inspection cannot answer.
4. Prefer tracer-bullet vertical slices over horizontal layer work. (See [planning-rules.md — Tracer-bullet planning](references/planning-rules.md#tracer-bullet-planning).)
5. Keep irreversible architecture decisions open as long as practical. (See [planning-rules.md — Keep decisions open](references/planning-rules.md#keep-decisions-open).)
6. Identify whether any task requires an ADR stub. If yes, read [adr-rules.md](references/adr-rules.md) before writing the stub.
7. Create prioritized tasks with dependencies and enough context to execute. Read [planning-rules.md — Priority and Dependencies](references/planning-rules.md#priority) for priority and dependency guidance.
8. Select test types. Read [test-selection.md](references/test-selection.md) before choosing unit, integration, smoke, E2E, regression, performance, security, usability, or observability tests.
9. Evaluate diagram merit for each task. Include a Mermaid diagram in the task's Context section only when the trigger condition is met: the relationship or flow cannot be expressed in ≤3 bullet points, or ≥3 components interact. Read [diagram-rules.md](references/diagram-rules.md) for diagram type selection, placement, and formatting.
10. Define requirements, acceptance criteria, and observability. If two requirements contradict each other, flag the conflict explicitly in the task under "Unresolved assumptions" — do not silently pick one interpretation. (See [planning-rules.md — Task sections](references/planning-rules.md#task-sections).)
11. Classify each task as **AFK** (can be completed autonomously by an agent without human review) or **HITL** (requires human involvement at a named decision point — state the decision). Read [planning-rules.md — HITL/AFK classification](references/planning-rules.md#hitlafk-classification) for criteria.
12. Write one Markdown issue file per task in `tasks/issues/`. Read [output-files.md](references/output-files.md) for naming conventions. Use [assets/task-template.md](assets/task-template.md) as the exact structure.
13. Write ADR stubs in `docs/adrs/` only when architecture decisions are needed. Use [assets/adr-template.md](assets/adr-template.md) as the exact structure.
14. If domain terms were defined or clarified during planning, add them to `CONTEXT.md` at the project root using the format in [assets/context-template.md](assets/context-template.md).

## Output files

Create one issue file per task in `tasks/issues/` and one ADR stub per decision in `docs/adrs/`.

```bash
mkdir -p tasks/issues docs/adrs
```

See [output-files.md](references/output-files.md) for numbering, naming, and ordering rules.

## Before marking complete

- [ ] Every issue file in `tasks/issues/` has no empty required sections
- [ ] Task numbering reflects dependency order (no task numbered before one it depends on)
- [ ] ADR stubs exist for every task that depends on an architectural decision
- [ ] Each task has an AFK or HITL classification with a named reason
- [ ] `CONTEXT.md` updated if domain terms were defined or clarified

## If output fails

If files cannot be created:
- Verify the directory exists: `ls -ld tasks/issues/` — if not, run `mkdir -p tasks/issues`
- Report the error and propose an alternative output location if needed.

## Anti-patterns to avoid

**Scope and composition**: Do not artificially split atomic work, duplicate content across sections (Context explains *why*, Use Cases describe *who/when*, Requirements define *what must be true*), or bundle a change with its validation step. Each task must leave the system fully functional — no task may remove behavior without replacing it in the same task.

**Inspect before asking; order by blocker**: Never ask the requester for information the codebase can answer. Inspect first. Dependency order takes precedence — a task that unblocks others must be numbered first.

**Right-size tests and decisions**: Mark a test category applicable only when the task genuinely requires it. Create an ADR only for decisions that are hard to reverse, cross-cutting, or architecture-level — not routine implementation details.

## Final response

After creating the files, summarize:

- created issue files
- created ADR files, if any
- task order
- ADR dependencies, if any
- unresolved assumptions, if any
- tests intentionally marked not applicable