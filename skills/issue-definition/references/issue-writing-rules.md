# Issue Writing Rules

Write issues so a reviewer can tell what will change, what will not change, and how completion will be judged.

## Core rules
- prefer observable language over intent-only language
- state behavior, not vibes
- name scope and non-goals explicitly
- make acceptance criteria falsifiable
- separate known facts from assumptions and open questions
- avoid pre-implementing the solution unless the solution is already decided

## Prefer observable wording
Weak:
- improve performance
- simplify the UX
- clean up the API

Better:
- reduce p95 response time for the affected endpoint under the defined workload
- reduce the checkout flow from 4 screens to 3 without removing confirmation details
- remove the unused field from the public API response while keeping existing required fields unchanged

## Anti-vague rules
Do not write:
- make it better
- fix the issue
- support this workflow
- refactor for maintainability
- handle edge cases

Instead write:
- what behavior is wrong now
- what behavior is expected instead
- which users or systems are affected
- what must remain unchanged
- which edge cases matter
- what evidence will show the change is complete

## Readiness-gap handling
If required information is missing:
- do not guess silently
- capture the gap explicitly
- place it under assumptions, open questions, or Definition of Ready
- keep the issue blocked only on gaps that materially affect safe implementation

Examples:
- Weak: add export support
- Better: add CSV export for the report summary table; PDF export is out of scope

- Weak: fix login bug
- Better: when a user enters valid credentials after a session timeout, the app should authenticate successfully instead of remaining on the loading state

- Weak: refactor notifications
- Better: extract notification delivery logic so email and in-app sending paths can be changed independently without changing user-visible behavior
