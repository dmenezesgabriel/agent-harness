---
id: "{{SLUG}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
status: draft
request-type: "{{new-product | new-feature | behavior-change}}"
---

# PRD: <feature or product name>

## Problem Statement

<2–4 sentences. What is broken, missing, or painful — and for whom. No solution language.>

Example:
- Team leads must open each project individually to see its current status. During stand-up they spend 10–15 minutes collecting status updates that should take under 2 minutes.

## Personas

| Persona | Role / Job-to-be-done | Pain point |
|---|---|---|
| <role name> | <specific job or responsibility> | <specific frustration or unmet need> |

Example:
| Team Lead | Runs daily stand-up and tracks cross-project status | Must open each project individually; no single-view summary |
| Developer | Receives status change notifications | Gets notified on projects they are not assigned to |

## User Stories

- **As a** <persona>, **I want** <concrete goal>, **so that** <specific benefit>.

Example:
- **As a** team lead, **I want** to see the status of all active projects on one page, **so that** I can run stand-up in under 2 minutes.
- **As a** developer, **I want** to receive notifications only for projects I am assigned to, **so that** I can focus on my own work.

## Success Metrics

| Metric | Baseline | Target | Measurement method |
|---|---|---|---|
| <metric name> | <current value or "unknown"> | <measurable target> | <how measured> |

Example:
| Time-to-status-summary during stand-up | 12 minutes (session replay) | Under 2 minutes | Session replay p50 |
| Developer notification relevance | Unknown | ≥80% of notifications are relevant | Post-release user survey |

## Constraints

- <Technical, business, compliance, or integration constraint explicitly stated or clearly implied by context.>

Example:
- Must integrate with the existing project permissions model — team leads see only projects they have access to.
- Must not require a pricing plan change for existing users.

## Non-Goals

- <What is explicitly out of scope and why.>

Example:
- Does not include mobile push notifications — web notifications only for this release.
- Does not redesign project detail pages — only the summary view is new.
- Does not cover external collaborator access — internal team members only.

## Open Questions

- <Question that blocks scope or success metric definition if unanswered.>
- None.

Example:
- Should the status view include archived projects, or only active ones?
- Does "status" include just task completion, or also blockers and last-updated timestamps?
