# Work-Type Examples

Load this reference only when the issue type is unclear or when the issue definition needs sharper examples.

## Feature / Improvement

Make these explicit:
- user or operator value
- new or changed behavior
- affected surfaces or workflows
- success criteria
- rollout or compatibility constraints when relevant

## Frontend

Make these explicit:
- visible states: loading, empty, success, error, disabled, invalid
- key user interactions
- accessibility expectations
- responsive or layout constraints
- visual or content constraints when they affect acceptance

## Backend

Make these explicit:
- domain rules and invariants
- API/event/request-response contracts
- persistence impact
- failure handling
- idempotency, concurrency, or consistency expectations when relevant

## Fullstack

Make these explicit:
- end-to-end flow
- boundary between frontend and backend
- contract crossing the seam
- sequencing if one side must land first

## Bugfix

Make these explicit:
- current behavior
- expected behavior
- reproduction conditions
- user/system impact
- regression-sensitive paths

## Refactor

Make these explicit:
- behavior that must not change
- design problem being improved
- migration or compatibility constraints
- safety boundaries for incremental change
