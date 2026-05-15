# Issue Writing Rules

Write issues so a reviewer can tell what changes, what stays unchanged, and how completion will be judged.

## Core rules
- classify every issue with both labels: `Surface` and `Work type`
- prefer observable language over intent-only language
- state behavior, not vibes
- name scope and non-goals explicitly
- separate facts, assumptions, and open questions
- avoid pre-implementing the solution unless it is already decided
- use the smallest issue shape that still makes implementation safe
- omit optional sections that add no decision-making value

## Omission discipline
- do not add context just to sound thorough
- do not add non-functional requirements without a material threshold or constraint
- do not add success metrics unless the issue is supposed to move a measurable outcome
- do not list open questions when none materially affect safe implementation
- in fork-specific notes, include only the relevant surface note and the relevant work-type note

## Prefer observable wording
Weak:
- improve performance
- simplify the UX
- clean up the API

Better:
- reduce p95 response time for the affected endpoint from 900ms to under 400ms under the defined workload
- reduce the checkout flow from 4 screens to 3 without removing confirmation details
- remove the unused field from the public API response while keeping existing required fields unchanged
- reject CSV uploads over 10MB with a clear error message instead of timing out

## Readiness-gap handling
If required information is missing:
- do not guess silently
- capture the gap explicitly
- place it under assumptions, open questions, or Definition of Ready
- keep the issue blocked only on gaps that materially affect safe implementation
