# Validation Routing

Route final validation by changed surface and work type. Start with the smallest sufficient proof set, then expand only when risk or failures justify it.

## Issue taxonomy to validation route

| Issue surface | Issue work type | Primary validation route |
| --- | --- | --- |
| Frontend | Feature / Improvement / Research-backed change | Frontend |
| Backend | Feature / Improvement / Research-backed change | Backend |
| Fullstack | Feature / Improvement / Research-backed change | Fullstack |
| Frontend / Backend / Fullstack | Bugfix | Bugfix depth plus the listed surface |
| Frontend / Backend / Fullstack | Refactor | Refactor depth plus the listed surface |

`Feature`, `Improvement`, and `Research-backed change` stay issue labels. Final validation still lands on a frontend, backend, or fullstack surface, with work type adding bugfix regression depth or refactor behavior-preservation depth on top of the listed surface.

## Small pure logic or isolated bugfix
Usually run:
- targeted unit or regression tests
- type check when the ecosystem uses it
- lint only if CI enforces it or the touched area commonly fails it

Usually skip:
- broad integration, E2E, or audit work unless the bug crosses those boundaries

## Backend change
Usually run:
- targeted unit tests for rules and invariants
- integration tests for handlers, services, persistence, or transactions
- contract or schema checks for request, response, or message boundaries
- type/build checks when relevant

Also verify:
- validation and error paths
- authorization or trust-boundary behavior when touched
- compatibility concerns such as migrations or state transitions when relevant

## Frontend change
Usually run:
- targeted component or behavior tests
- accessibility-focused checks when semantics, labels, focus, keyboard behavior, or errors changed
- integration checks for connected flows, routing, or data loading when touched
- type/build checks when relevant

Also verify:
- user-visible behavior and acceptance scenarios
- loading, empty, success, error, disabled, and invalid states as relevant
- critical flows only if the change touches them

## Fullstack or seam/contract change
Usually run:
- targeted frontend and backend checks at their owning boundaries
- integration or contract checks for the seam between them
- type/build checks when either side depends on them
- critical user-flow verification only for the changed path

Also verify:
- request/response or message contract compatibility
- loading, empty, success, error, disabled, and invalid states when visible behavior changed
- sequencing or migration concerns when one side must land before the other

## Cross-cutting or high-risk change
Usually run:
- targeted tests plus adjacent integration coverage
- lint, type, and build checks
- smoke or critical-flow checks where the risk is user-visible or system-critical
- specialist audits only when the change or request justifies them

Examples:
- auth or authorization
- payments or financial rules
- data integrity or migrations
- shared libraries used widely
- build, config, or dependency changes
