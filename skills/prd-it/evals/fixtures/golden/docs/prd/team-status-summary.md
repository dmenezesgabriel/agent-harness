---
id: "team-status-summary"
created: 2026-06-01
updated: 2026-06-01
status: draft
request-type: "new-feature"
---

# PRD: Team status summary

## Problem Statement

Team leads at project-based agencies must open each active project one by one before stand-up to understand status, blockers, and overdue work. This takes 10-15 minutes every morning and causes missed blockers when a project is skipped.

## Personas

| Persona | Role / Job-to-be-done | Pain point |
|---|---|---|
| Team Lead | Prepares for daily stand-up across active projects | Spends 10-15 minutes collecting status and can miss blockers |

## User Stories

- **As a** team lead, **I want** to understand active project status before stand-up, **so that** I can prepare in under 3 minutes.
- **As a** team lead, **I want** blocker visibility across active projects, **so that** skipped projects do not hide urgent work.

## Success Metrics

| Metric | Baseline | Target | Measurement method |
|---|---|---|---|
| Time-to-status-summary during stand-up preparation | 12 minutes | Under 3 minutes | Pilot-team session replay p50 |
| Missed blocker reports after stand-up | Unknown | 25% reduction within 30 days | Pilot-team blocker follow-up survey |

## Constraints

- Existing project permissions must still apply.
- The first release should not send developers extra notifications.

## Non-Goals

- Does not add developer notifications — the brief excludes extra notifications for this release.
- Does not define architecture or implementation plan — this PRD covers product scope only.

## Open Questions

- Should archived projects appear in the status summary, or only active projects?
