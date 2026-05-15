# Issue template

Use the smallest issue shape that still makes implementation safe.

## Required core sections

Include these in every issue:

```md
### Issue: <precise title>

Surface:
Frontend | Backend | Fullstack

Work type:
Feature | Bugfix | Refactor | Improvement | Research-backed change

Implementation route hint:
Backend TDD | Frontend component-driven | Fullstack seam-splitting | Bugfix workflow | Refactor workflow

Final validation route hint:
Frontend | Backend | Fullstack | Bugfix depth on the listed surface | Refactor depth on the listed surface

Problem / Request:
<what is happening now, or what is being requested>

Goal:
<desired outcome in observable terms>

Scope:
- <included item>

Non-goals:
- <explicitly excluded item>

Acceptance criteria:
- <observable outcome>

Task slices:
1. <smallest first slice>
2. <next slice>
```

## Add when needed

Only include a section if it changes implementation, sequencing, or validation.

```md
Why now:
<why this matters now>

Context:
<relevant user, business, technical, or operational context>

Assumptions:
- <fact not yet confirmed but used to shape the issue>

Dependencies / Constraints:
- <upstream system / API / contract / rollout / sequencing / environment constraint>

Functional requirements:
- <observable system behavior>

Non-functional requirements:
- <performance / accessibility / security / reliability threshold>

Fork-specific notes:
- Frontend: <states / interactions / accessibility / responsive constraints>
- Backend: <rules / contracts / persistence / failure handling>
- Fullstack: <end-to-end flow / seam contract / sequencing>
- Work type: <repro / preserved behavior / improvement target / research finding>

Use cases:
- <primary flow>

Edge cases:
- <failure mode / boundary condition / empty state / invalid input / regression-sensitive case>

Risks:
- <product / technical / migration / UX / data / security / performance / delivery risk>

Definition of Ready:
- <precondition required before implementation should start>

Definition of Done:
- <condition required for completion>

Validation expectations:
- <expected implementation-time protections>
- <expected final merge-readiness checks>

Success metrics:
- <metric to move, baseline if known, target, measurement window>

Open questions:
- <only unresolved items that materially affect implementation>
```

## Omission rules

- Do **not** fill every optional section by default.
- Omit `Why now` when urgency is obvious from the request.
- Omit `Context` unless it sharpens scope or tradeoffs.
- Omit `Non-functional requirements` unless thresholds materially matter.
- Omit `Success metrics` unless the issue is meant to move adoption, speed, reliability, quality, or support load.
- Omit `Open questions` when there are no material unknowns.
- In `Fork-specific notes`, include only the relevant surface note and the relevant work-type note.

## Minimal issue shape

Use the required core sections alone when the request is already clear and low-ambiguity but still needs issue framing.

Typical fit:
- small feature with obvious scope
- improvement with clear unchanged boundaries
- bugfix with known repro and narrow impact

## Fuller issue shape

Add optional sections when the request has meaningful unknowns, higher coordination cost, stricter safety needs, or cross-team constraints.

Typical fit:
- fullstack work with seam contracts
- bugfixes with unclear root cause or regression risk
- refactors with strict behavior-preservation boundaries
- research-backed changes where evidence and rationale matter
- work with rollout, dependency, reliability, accessibility, or performance constraints
