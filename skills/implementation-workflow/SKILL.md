---
name: implementation-workflow
description: Use this skill when implementing a scoped change in an existing codebase: backend rule or API change, frontend component or interaction, bugfix, refactor, or fullstack feature. It classifies the change and routes to the right workflow: Backend TDD for backend/domain-heavy work, Frontend component-driven for frontend/UI-heavy work, Fullstack seam-splitting for fullstack changes, Bugfix workflow for reproduce-first correction, and Refactor workflow for behavior-protecting characterization. Do not use when the work is still vague and needs issue definition, or when the main task is final merge validation.
---

## Purpose

Implement a defined change in an existing codebase using the right workflow for the change shape.

This skill is for focused implementation plus short, change-tied validation. It is not a broad audit or final review workflow.

Use `skills/issue-definition` first when the request still needs scope, acceptance criteria, Definition of Ready, or task slices. Use `skills/change-validation` after implementation when the main goal is merge-readiness verification.

Use `assets/implementation-report-template.md` as the default output structure.
Use `scripts/recommend_route.py` only when route selection is unclear or repeated often enough to justify a helper; the written routing guidance remains primary.

## Use This Skill When

Use this skill when the request is to implement a scoped change such as:

- backend rule, validation, policy, persistence, or API behavior
- frontend component, interaction, state, or accessibility behavior
- fullstack feature crossing UI and backend boundaries
- bugfix with a repro or regression path
- refactor that should preserve behavior

## Do Not Use This Skill When

Do not use this skill when:

- the task is still vague and needs issue definition or scoping first
- the main job is broad review, deep audit, or final merge validation
- the request is primarily architecture exploration rather than implementation

## Route Summary

Classify the change before coding. Pick the route that matches the main risk and first protection.

- **Backend TDD** — backend/domain rules, invariants, policy, service logic, or persistence-heavy behavior. Start with a failing behavior test. See `references/backend-tdd-route.md` and `references/tdd-reference.md`.
- **Frontend component-driven** — user-visible behavior, state, interaction, rendering, or accessibility. Start from visible states and behavior scenarios. See `references/frontend-component-driven-route.md` and `references/component-driven-design.md`.
- **Fullstack seam-splitting** — one change crosses UI plus API/domain boundaries. Define the seam/contract first, then protect both sides. See `references/fullstack-seam-splitting.md`.
- **Bugfix workflow** — existing incorrect behavior or regression. Reproduce first, then add regression protection. See `references/bugfix-workflow.md`.
- **Refactor workflow** — structure, ownership, cohesion, or dependency direction should improve while behavior stays the same. Protect behavior first. See `references/refactor-workflow.md`.

For route selection details and tie-breakers, see `references/change-routing.md`.
For design checks during implementation, see `references/software-design-principles.md`.

## Smallest Safe Implementation Loop

1. Classify the change and choose the route.
2. Confirm the required behavior, acceptance criteria, constraints, and non-goals.
3. Identify the owning boundary.
4. Add the first protection that fits the route:
   - failing behavior test
   - visible behavior scenario
   - repro plus regression test
   - characterization coverage
5. Implement the smallest passing change.
6. Refactor only while protection stays green.
7. Run short targeted validation tied to the changed behavior.
8. Report what changed, what was validated, and any remaining risk.

## Validation Expectations and Boundaries

Keep validation short and relevant during implementation:

- run targeted checks for the changed behavior
- include regression coverage for bugs
- include seam or contract checks when boundaries changed
- include accessibility or UI-state checks for frontend behavior when relevant
- use broader suites only when the change materially justifies them

Use one-off commands with existing tooling by default. Scripts are optional helpers, not the primary routing mechanism. Hand off to `skills/change-validation` when the request is primarily final validation rather than implementation.
Read `references/validation-examples.md` only when you need concrete command defaults.

## Assets, Scripts, and References

- output template: `assets/implementation-report-template.md`
- optional route helper: `scripts/recommend_route.py`
- routing reference: `references/change-routing.md`
- backend route: `references/backend-tdd-route.md`
- frontend route: `references/frontend-component-driven-route.md`
- fullstack route: `references/fullstack-seam-splitting.md`
- bugfix route: `references/bugfix-workflow.md`
- refactor route: `references/refactor-workflow.md`
- design principles: `references/software-design-principles.md`
- TDD reference: `references/tdd-reference.md`
- component-driven design reference: `references/component-driven-design.md`
- validation examples: `references/validation-examples.md`
