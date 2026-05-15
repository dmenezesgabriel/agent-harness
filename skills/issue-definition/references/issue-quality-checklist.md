# Issue Quality Checklist

Use this as a final pass before calling an issue implementation-ready.

A good issue definition makes these explicit:

## Core framing
- the exact problem, request, or behavior change
- why it matters
- who or what is affected
- the desired outcome in observable terms

## Scope control
- what is in scope
- what is out of scope
- assumptions that shape the work
- known dependencies or constraints

## Requirements
- functional requirements: what the system must do
- non-functional requirements only when relevant: performance, accessibility, security, reliability, compatibility, observability, maintainability
- important use cases and edge cases

## Delivery readiness
- risks or unknowns that could block safe implementation
- Definition of Ready: what must be resolved before coding starts
- Definition of Done: what must be true to call the issue complete
- validation expectations: what kinds of checks should exist during implementation

## Completion criteria
- acceptance criteria written as observable outcomes
- task slices small enough to implement incrementally
- open questions listed only when they materially affect implementation

## Quick fail checks
The issue is not ready if it still says things like:
- improve this area
- clean up the code
- make it better
- fix the bug
- add the feature
- refactor for maintainability

Replace vague wording with:
- what changes
- what stays unchanged
- how completion will be judged
- what evidence will show the work is done
