# Change Routing

## Purpose

Use this reference to choose the implementation route before coding.

Pick the route that matches the main risk and the first protection you need while implementing.

## Issue taxonomy to implementation route

| Issue surface | Issue work type | Primary implementation route |
| --- | --- | --- |
| Frontend | Feature / Improvement / Research-backed change | Frontend component-driven |
| Backend | Feature / Improvement / Research-backed change | Backend TDD |
| Fullstack | Feature / Improvement / Research-backed change | Fullstack seam-splitting |
| Frontend / Backend / Fullstack | Bugfix | Bugfix workflow first; preserve the listed surface for owning-boundary checks |
| Frontend / Backend / Fullstack | Refactor | Refactor workflow first; preserve the listed surface for behavior protection |

`Feature`, `Improvement`, and `Research-backed change` shape the issue. They do not replace the implementation routes.

## Available routes

- **Backend TDD** — backend, domain, rule, validation, policy, persistence, or service-heavy change
- **Frontend component-driven** — user-visible behavior, component state, interaction, rendering, or accessibility-heavy change
- **Fullstack seam-splitting** — one change crosses UI plus API/domain/persistence boundaries
- **Bugfix workflow** — existing incorrect behavior must be reproduced and protected against regression
- **Refactor workflow** — structure must improve while behavior stays the same

## Route-selection signals

### Choose Backend TDD when
- the core change is a rule, invariant, policy, calculation, transition, or contract on the backend
- transport or framework code is thin compared with the business logic
- the safest first step is a failing behavior test at the owning backend boundary

### Choose Frontend component-driven when
- the core change is visible in the UI
- success depends on states, interactions, rendering, composition, or accessibility
- the safest first step is a behavior scenario around what the user can see or do

### Choose Fullstack seam-splitting when
- one flow crosses frontend and backend boundaries
- UI and API/domain must change together
- the main risk is an unclear contract between layers

### Choose Bugfix workflow when
- behavior is already wrong in production, test, or local use
- you have repro steps, an observed failure, or a regression path
- the first need is to make the failure repeat reliably

### Choose Refactor workflow when
- the request is mainly about structure, ownership, naming, coupling, or boundaries
- behavior should remain unchanged
- the main risk is breaking existing behavior while cleaning up

## How to choose

1. Ask: **Is this mainly a bugfix or mainly a refactor?**
   - If yes, use that route first.
2. If not, ask: **Is the center of gravity backend, frontend, or both?**
   - backend-heavy -> Backend TDD
   - frontend-heavy -> Frontend component-driven
   - both with a crossing contract -> Fullstack seam-splitting
3. Choose the route whose **first protection** best matches the risk.
4. If the change mixes concerns, still pick one primary route and use the others only where the seam requires it.
5. Choose the route that lets you protect the most important behavior at the highest stable boundary first.

## Tie-breakers

- New backend rule behind an existing API -> Backend TDD
- New UI state backed by unchanged data -> Frontend component-driven
- New user flow requiring UI and API changes -> Fullstack seam-splitting
- Regression caused by any layer -> Bugfix workflow
- Cleanup discovered during implementation -> only refactor after behavior is protected
