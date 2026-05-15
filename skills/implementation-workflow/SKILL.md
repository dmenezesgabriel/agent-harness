---
name: implementation-workflow
description: "Use this skill when implementing an implementation-ready, scoped change in an existing codebase: backend rule or API change, frontend component or interaction, bugfix, refactor, or fullstack feature. It classifies the change and routes to the right workflow: Backend TDD for backend/domain-heavy work, Frontend component-driven for frontend/UI-heavy work, Fullstack seam-splitting for fullstack changes, Bugfix workflow for reproduce-first correction, and Refactor workflow for behavior-protecting characterization. Do not use when the work is still vague, bundles unrelated changes that need slicing, or when the main task is final merge validation."
---

## Purpose

Implement a defined change in an existing codebase using the right workflow for the change shape.

This skill is for focused implementation plus local proof that the change works at its owning boundary. It is not the final merge-readiness validation workflow.

Use `skills/issue-definition` first when the request still needs scope, acceptance criteria, Definition of Ready, or task slices. Use `skills/change-validation` after implementation when the main goal is final verification of acceptance criteria, Definition of Done, and merge readiness.

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

## Workflow mapping

Consume the issue taxonomy explicitly before coding:

| Issue surface | Issue work type | Primary implementation route |
| --- | --- | --- |
| Frontend | Feature / Improvement / Research-backed change | Frontend component-driven |
| Backend | Feature / Improvement / Research-backed change | Backend TDD |
| Fullstack | Feature / Improvement / Research-backed change | Fullstack seam-splitting |
| Frontend / Backend / Fullstack | Bugfix | Bugfix workflow first; keep the listed surface for owning-boundary protection |
| Frontend / Backend / Fullstack | Refactor | Refactor workflow first; keep the listed surface for behavior protection |

`Surface` tells you where the change lives. `Work type` tells you what kind of protection to add first. `Feature`, `Improvement`, and `Research-backed change` are issue labels, not separate implementation routes.

## Workflow

1. Confirm the request is implementation-ready. If scope, acceptance criteria, or task slicing are still unclear, or the request bundles unrelated changes, use `skills/issue-definition` first.
2. Read the issue taxonomy. Record the incoming `Surface` and `Work type`, then choose the implementation route that matches the main risk and first protection.
3. Read only the route references needed for the chosen route plus any design references the change actually needs.
4. Follow the route-specific protection-first loop: add the first protection at the owning boundary, implement the smallest passing change, and keep validation tied to the changed behavior.
5. Report using `assets/implementation-report-template.md` by default, including what changed, what local proof was run, and what final validation should happen next.

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

1. Confirm the required behavior, acceptance criteria, constraints, and non-goals.
2. Identify the owning boundary.
3. Add the first protection that fits the route:
   - failing behavior test
   - visible behavior scenario
   - repro plus regression test
   - characterization coverage
4. Implement the smallest passing change.
5. Refactor only while protection stays green.
6. Run short targeted checks tied to the changed behavior.
7. Report what changed, what local proof passed, and any remaining risk that final validation must evaluate.

## Validation Expectations and Boundaries

Implementation-time validation exists to prove the edit locally while coding, not to replace final merge-readiness review.

During implementation:

- run targeted checks for the changed behavior
- include regression coverage for bugs
- include seam or contract checks when boundaries changed
- include accessibility or UI-state checks for frontend behavior when relevant
- use broader suites only when the implementation route materially requires them

Do not treat the implementation report as final signoff. It should capture developer-confidence evidence and the recommended next validation scope.

Use one-off commands with existing tooling by default. Scripts are optional helpers, not the primary routing mechanism. Read `references/validation-examples.md` only when you need concrete command defaults.

## Handoff to change-validation

Hand off to `skills/change-validation` when:
- the requested code change is implemented
- route-local protections and targeted checks are green, or any remaining failures are explicitly reported
- the next question is merge readiness rather than how to finish the implementation
- acceptance criteria and Definition of Done now need final confirmation across the relevant surface

## Exit criteria

This skill is complete when:
- the implementation route is explicit and matches the issue taxonomy
- the code change is complete for the scoped slice
- local proof exists at the owning boundary
- targeted implementation-time checks are recorded
- remaining work is clearly final validation, broader readiness checks, or an explicit blocked risk

## Edge Cases

- If a task looks fullstack but most risk sits in an existing bug or regression, use the bugfix workflow first and add seam checks only where the fix crosses boundaries.
- If a task mixes refactor plus feature work, choose the route for the behavior that needs first protection, then keep pure refactor steps behind green coverage.
- If the request bundles multiple unrelated implementation slices, stop and send it to `skills/issue-definition` for slicing instead of forcing one route.
- If the codebase has no obvious fast test hook, add the narrowest protection you can at the owning boundary before reaching for a broader end-to-end suite.
- If route selection is still ambiguous after reading `references/change-routing.md`, use `scripts/recommend_route.py` as a helper; do not let the script replace written judgment.

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
