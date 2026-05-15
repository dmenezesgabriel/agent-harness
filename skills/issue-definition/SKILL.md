---
name: issue-definition
description: Use this skill when a user has an idea, bug, request, feature, improvement, refactor, cleanup, or vague change and needs it turned into a clear issue, task definition, acceptance criteria, scope, risks, and implementation-ready slices. Do not use when the work is already clearly scoped and needs coding or post-change verification.
---

## Purpose

Turn a request into a crisp, implementation-ready issue definition.

Use this skill to define work for feature requests, bug reports, refactors, technical improvements, UX changes, backend work, frontend work, fullstack work, and unclear asks that need framing before coding.

This skill defines work. It does not implement code or run validation.

After the issue is ready, implementation belongs in `skills/implementation-workflow`. Post-change verification and merge-readiness checks belong in `skills/change-validation`.

## When to use / not use

Use it when the request is still ambiguous and needs a precise title, problem statement, scope, non-goals, acceptance criteria, readiness, risks, validation expectations, or task slices.

Do not use it when the work is already clearly scoped and the next step is implementation, execution, or post-change verification.

## Work-type routing

Route by work type only when it improves clarity:

- **Frontend**: emphasize UI behavior, states, accessibility, and interaction flows
- **Backend**: emphasize domain rules, APIs, data flow, persistence, and failure handling
- **Fullstack**: emphasize end-to-end flow and frontend/backend contract boundaries
- **Bugfix**: emphasize current vs expected behavior, repro conditions, impact, and regression risk
- **Refactor**: emphasize preserved behavior, design problem, constraints, and safety boundaries

Do not force multiple tracks if one issue definition is enough.

## Framing expectations

Keep the issue concrete, observable, and safe to implement.

At minimum, make the problem or request, goal, scope, non-goals, acceptance criteria, validation expectations, and task slices explicit. If key information is missing, record it as an assumption, open question, or Definition of Ready gap instead of guessing.

Use the issue template as the default output shape. Keep solution detail only as far as it is already decided; the goal is to remove ambiguity, not pre-implement the work.

## Assets, scripts, and references

- Default template: `assets/issue-template.md`
- Optional helper script: `scripts/classify_issue.py`
  - Use only when issue typing is unclear or repeated often enough that lightweight automation helps.
  - Description-first routing remains the default; the script is a helper, not the primary router.
- References:
  - `references/issue-quality-checklist.md`
  - `references/issue-definition-process.md`
  - `references/issue-writing-rules.md`
  - `references/work-type-examples.md`

Reach for the references when you need the deeper checklist, full process, stronger writing rules, or work-type-specific examples.