---
id: "{{NUMBER}}"
issue: "{{issues/NNN-slug.md}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
---

# Review: <task name>

## Related Task

- `<issues/NNN-slug.md>`

## Overall Verdict

**<Pass | Fail>**

<If Pass: no Blocking findings.>
<If Fail: Blocked by F-NNN, F-NNN. Implementer must resolve all Blocking findings before mark-complete.>

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Blocking | AC-001 | <what is wrong> | `<file:line>` |
| F-002 | Non-blocking | OBS-001 | <what is missing or partial> | `<file:line>` |
| F-003 | Suggestion | — | <optional improvement> | `<file:line>` |

<If no findings at a level, omit those rows or write "None.">

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | <brief evidence — e.g., file created at reviews/NNN-slug-review.md> |
| AC-002 | Fail | <what is missing or incorrect — links to F-NNN> |
| AC-003 | Pass | <brief evidence> |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present / Missing | <file path if present; reason if missing or not applicable> |
| Integration (IT-001) | Present / Missing | <file path if present; reason if missing or not applicable> |
| Smoke (SMK-001) | Present / Missing | <confirmation or reason> |
| E2E | Not applicable | <reason from issue> |
| Regression | Not applicable | <reason from issue> |
| Performance | Not applicable | <reason from issue> |
| Security | Not applicable | <reason from issue> |
| Usability (UX-001) | Present / Missing | <confirmation or reason> |
| Observability | Not applicable | <reason from issue> |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | <requirement text> | Met / Partial / Missing | <evidence or gap> |

<If all OBS requirements are Not applicable in the issue, write: "Not applicable — no OBS requirements defined in the task.">

## ADR Compliance

| ADR | Required Action | Status |
|-----|-----------------|--------|
| `docs/adrs/NNN-slug.md` | Updated from Proposed to Accepted | Done / Not done |

<If no ADRs listed under task Dependencies, write: "Not applicable — no ADR dependencies listed in the task.">

## Convention Notes

<Describe any Non-blocking or Suggestion findings from convention evaluation here. Reference finding IDs (F-NNN) for traceability. If no convention findings, write "None.">

Example:
- `F-003` — Suggestion — `scripts/ensure-reviews-dir.sh` duplicates the mkdir logic from `ensure-issues-dir.sh`. Could be unified, but not required by the task.

## Unresolved Assumptions or Follow-Up

- <Assumption or gap not covered by this review>
- None.

Example:
- The smoke test (SMK-001) was not run manually because the skill is not yet registered in settings.json. Follow-up: register and run.
- AC-008 (missing issue file prompt) was not verifiable from the code diff alone — requires live invocation to confirm.
