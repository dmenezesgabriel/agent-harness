# Issue Quality Checklist

Use this as a final pass before calling an issue implementation-ready.

## Must be true
- surface is named: Frontend, Backend, or Fullstack
- work type is named: Feature, Bugfix, Refactor, Improvement, or Research-backed change
- problem or request is explicit in observable terms
- scope and non-goals are clear
- acceptance criteria are observable and falsifiable
- task slices are small enough to start implementation safely

## Boundary and fork checks
- assumptions are separated from facts when needed
- dependencies or constraints are named when they affect sequencing or safety
- the issue includes the relevant surface details:
  - Frontend: states, interactions, accessibility, responsive constraints
  - Backend: rules, contracts, persistence, failure handling
  - Fullstack: end-to-end flow, seam contract, sequencing
- the issue includes the relevant work-type details:
  - Bugfix: repro and expected behavior
  - Refactor: preserved behavior and safety boundary
  - Improvement: observable improvement target and unchanged boundary
  - Research-backed change: evidence source and rationale

## Optional sections stay optional
- non-functional requirements appear only when relevant
- success metrics appear only when meaningful
- open questions appear only when they materially affect implementation
- omitted sections do not leave material ambiguity

## Quick fail checks
The issue is not ready if it still says things like:
- improve this area
- clean up the code
- make it better
- fix the bug
- add the feature
- refactor for maintainability
