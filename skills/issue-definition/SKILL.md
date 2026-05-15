---
name: issue-definition
description: Use this skill when a user has an idea, bug, request, feature, improvement, refactor, cleanup, or vague change and needs it turned into a clear issue, task definition, acceptance criteria, scope, risks, and implementation-ready slices. Do not use when the work is already clearly scoped and needs coding or post-change verification.
---

## Purpose

Turn ambiguous requests into implementation-ready issue definitions with clear scope, acceptance criteria, and task slices.

This skill defines work. It does not implement code or run validation.

## Workflow

1. **Clarify the request.** Understand what the user is asking. Identify the work type — feature, bugfix, refactor, improvement, frontend, backend, fullstack, or unclear. Read `references/work-type-examples.md` if the type is unclear.
   - **Frontend**: emphasize UI behavior, states, accessibility, and interaction flows
   - **Backend**: emphasize domain rules, APIs, data flow, persistence, and failure handling
   - **Fullstack**: emphasize end-to-end flow and frontend/backend contract boundaries
   - **Bugfix**: emphasize current vs expected behavior, repro conditions, impact, and regression risk
   - **Refactor**: emphasize preserved behavior, design problem, constraints, and safety boundaries
   - If the type is still unclear after description-first routing, run `scripts/classify_issue.py` for lightweight signal extraction.

2. **Frame the issue.** Write a precise title. State the problem or request in observable terms. Record context — who is affected, where it happens, why it matters now.

3. **Set scope.** Define what is in scope and what is explicitly excluded. Record assumptions that shape the work. Note known dependencies or constraints.

4. **Write requirements.** List functional requirements (what the system must do). Add non-functional requirements (performance, accessibility, security) only when they materially matter. Cover primary flows and edge cases — failure modes, empty states, invalid input, regression-sensitive paths.

5. **Define completion gates.** Write acceptance criteria as observable outcomes (use Given/When/Then when it helps clarity). Set Definition of Ready (what must be true before implementation starts) and Definition of Done (what must be true for completion). State validation expectations — what tests, checks, demos, or review points should exist during implementation.

6. **Slice the work.** Break the issue into the smallest meaningful implementation steps that can be built and verified independently.

7. **Surface gaps.** If key information is missing, record it under assumptions, open questions, or Definition of Ready instead of guessing. List risks — product, technical, migration, UX, data, security, performance, delivery.

8. **Write the output.** Use `assets/issue-template.md` as the default shape. Keep solution detail only as far as it is already decided. After the issue is ready, pass it to `skills/implementation-workflow` for coding or `skills/change-validation` for post-merge review.

## When to use / not use

Use it when the request is still ambiguous and needs a precise title, problem statement, scope, non-goals, acceptance criteria, readiness, risks, validation expectations, or task slices.

Do not use it when the work is already clearly scoped and the next step is implementation, execution, or post-change verification.

## References

- `references/issue-quality-checklist.md` — final pass before calling an issue ready
- `references/issue-definition-process.md` — full sequence with 12 detailed steps
- `references/issue-writing-rules.md` — observable language, anti-vague patterns, readiness-gap handling
- `references/work-type-examples.md` — type-specific framing guidance
- `assets/issue-template.md` — default output shape