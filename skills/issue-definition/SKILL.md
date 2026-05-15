---
name: issue-definition
description: Use this skill when a request is still vague and needs to become an implementation-ready issue. It classifies the work by Surface and Work type, sets scope and boundaries, and defines acceptance criteria, readiness gates, and task slices. Do not use when the work is already clearly scoped for implementation or is ready for post-change validation.
---

## Purpose

Turn ambiguous requests into concise, implementation-ready issues.

This skill defines work. It does not implement code or validate completed changes.

## Fast route

1. **Classify the request with both labels.**
   - **Surface**: Frontend | Backend | Fullstack
   - **Work type**: Feature | Bugfix | Refactor | Improvement | Research-backed change
2. **Map the downstream route.**
   - Frontend → frontend component-driven build, frontend validation
   - Backend → backend TDD build, backend validation
   - Fullstack → seam-split build, fullstack validation
   - Bugfix / Refactor → keep the surface, but add bugfix regression depth or refactor behavior-preservation depth
3. **Write only the issue shape the request needs.**
   - Always include the core sections from `assets/issue-template.md`.
   - Add optional sections only when they materially change implementation or validation.
4. **Make implementation possible without guesswork.**
   - Define observable scope, non-goals, acceptance criteria, validation expectations, and small task slices.
   - Put unresolved material gaps under assumptions, open questions, or Definition of Ready.

If classification is unclear, read `references/work-type-examples.md`. Use `scripts/classify_issue.py` only as a last pass for lightweight signal extraction.

## Taxonomy and workflow mapping

### Surface
- **Frontend**: UI behavior, states, copy, accessibility, interaction flow, layout.
- **Backend**: rules, APIs, jobs, data flow, persistence, failure handling.
- **Fullstack**: user-visible flow crosses the frontend/backend seam.

### Work type
- **Feature**: add net-new behavior.
- **Bugfix**: restore expected behavior.
- **Refactor**: improve structure without changing intended behavior.
- **Improvement**: improve an existing workflow, quality, or operational characteristic.
- **Research-backed change**: implement a change justified by research, evidence, or a prior investigation.

| Surface | Work type | Implementation route hint | Final validation route hint |
| --- | --- | --- | --- |
| Frontend | Feature / Improvement / Research-backed change | Frontend component-driven | Frontend |
| Backend | Feature / Improvement / Research-backed change | Backend TDD | Backend |
| Fullstack | Feature / Improvement / Research-backed change | Fullstack seam-splitting | Fullstack |
| Frontend / Backend / Fullstack | Bugfix | Bugfix workflow first; keep the listed surface for owning boundary checks | Bugfix depth plus the listed surface |
| Frontend / Backend / Fullstack | Refactor | Refactor workflow first; keep the listed surface for behavior protection | Refactor depth plus the listed surface |

`Surface` persists through issue definition, implementation, and final validation. `Work type` adds bugfix or refactor depth on top of the listed surface. `Feature`, `Improvement`, and `Research-backed change` shape the issue but do not override the surface route.

## Workflow

1. **Classify** the request with both labels.
2. **State the route** using the workflow mapping.
3. **Frame the issue** with a precise title, observable problem/request, goal, and why now.
4. **Set boundaries**: scope, non-goals, assumptions, dependencies, constraints.
5. **Write requirements**: functional first; non-functional only when material.
6. **Add only the applicable fork details**:
   - Frontend: states, interactions, accessibility, responsive behavior.
   - Backend: rules, contracts, data impact, failure handling.
   - Fullstack: end-to-end flow, seam contract, sequencing.
   - Bugfix: repro, impact, regression-sensitive path.
   - Refactor: preserved behavior, design problem, safety boundary.
   - Improvement: what gets better, how observed, what stays unchanged.
   - Research-backed change: evidence source, rationale, intended effect.
7. **Define completion** with acceptance criteria, Definition of Ready, Definition of Done, and validation expectations.
8. **Add success metrics only when meaningful.**
9. **Slice the work** into the smallest meaningful implementation steps.
10. **Write the output** using `assets/issue-template.md`, omitting optional sections that do not help.

## Exit criteria

This skill is complete when:
- `Surface` and `Work type` are explicit
- the downstream implementation route and final validation shape are stated
- scope and boundaries are usable without guesswork
- acceptance criteria and validation expectations are present
- task slices are small enough for implementation to begin safely

## When to use / not use

Use it when the request still needs scope, boundaries, acceptance criteria, readiness gates, or task slices.

Do not use it when the work is already clearly scoped for implementation or the next step is validating a completed change.

## References

- `assets/issue-template.md` — tiered issue template with required core sections and optional sections
- `references/issue-definition-process.md` — compact drafting sequence and minimal-vs-full guidance
- `references/issue-writing-rules.md` — wording rules, omission discipline, and anti-vague patterns
- `references/issue-quality-checklist.md` — final readiness check
- `references/work-type-examples.md` — classification examples for surfaces and work types
