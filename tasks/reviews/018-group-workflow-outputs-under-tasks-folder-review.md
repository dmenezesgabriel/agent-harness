---
id: "018"
issue: "tasks/issues/018-group-workflow-outputs-under-tasks-folder.md"
created: 2026-05-21
updated: 2026-05-21
---

# Review: Group workflow outputs under tasks/ folder

## Related Task

- `tasks/issues/018-group-workflow-outputs-under-tasks-folder.md`

## Overall Verdict

**Pass**

No Blocking findings.

## Findings

None.

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `skills/plan-it/scripts/ensure-issues-dir.sh`: `ISSUES_DIR="${1:-tasks/issues}"` → prints `ready: tasks/issues` on no-arg invocation. |
| AC-002 | Pass | `skills/plan-it/scripts/next-issue-number.sh`: `ISSUES_DIR="${2:-tasks/issues}"`, `ARCHIVE_DIR="${3:-tasks/issues/_archive}"` — correct defaults. |
| AC-003 | Pass | `skills/implement-it/scripts/ensure-implementation-dir.sh`: `IMPLEMENTATION_DIR="${1:-tasks/implementation}"` → prints `ready: tasks/implementation`. |
| AC-004 | Pass | `skills/review-it/scripts/ensure-reviews-dir.sh`: `REVIEWS_DIR="${1:-tasks/reviews}"` → prints `ready: tasks/reviews`. |
| AC-005 | Pass | `skills/plan-it/SKILL.md` uses `tasks/issues/` throughout issue examples; ADR examples use `docs/adrs/` unchanged. |
| AC-006 | Pass | `skills/implement-it/SKILL.md` uses `tasks/implementation/` throughout (lines 59–71 confirmed). |
| AC-007 | Pass | `skills/review-it/SKILL.md` uses `tasks/reviews/`, `tasks/issues/`, and `tasks/implementation/` throughout (confirmed by grep). |
| AC-008 | Pass | `skills/implement-it/assets/implementation-summary-template.md` frontmatter uses `tasks/issues/001-slug.md`; Related Task example uses `tasks/issues/001-example-task.md`. |
| AC-009 | Pass | `skills/review-it/assets/review-report-template.md` frontmatter uses `tasks/issues/NNN-slug.md`; findings table and Related Task example use `tasks/issues/` and `tasks/reviews/`. |
| AC-010 | Pass | `skills/plan-it/references/output-files.md` uses `tasks/issues/` throughout; `docs/adrs/` examples are unchanged. |
| AC-011 | Pass | `skills/review-it/references/review-rules.md` uses `tasks/issues/` and `tasks/reviews/` in all examples (confirmed by grep). |
| AC-012 | Pass | `skills/plan-it/assets/adr-template.md` Related Tasks example uses `tasks/issues/001-example-task.md`. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001–UT-004) | Present | Scripts confirmed correct by direct inspection; defaults verified in source. Implementation summary reports all four pass on manual invocation. |
| Integration | Not applicable | No integrated system behavior to test. |
| Smoke | Not applicable | No service or startup path involved. |
| E2E | Not applicable | No user journey through a running application. |
| Regression | Not applicable | No prior defect being fixed. |
| Performance | Not applicable | Script execution time is negligible. |
| Security | Not applicable | No trust boundaries involved. |
| Usability | Not applicable | No UI. |
| Observability | Not applicable | No logs, metrics, or traces. |

## Observability Evaluation

Not applicable — no OBS requirements defined in the task.

## ADR Compliance

| ADR | Required Action | Status |
|-----|-----------------|--------|
| `docs/adrs/001-separate-workflow-artifacts-from-adrs.md` | Updated from Proposed to Accepted | Done — Status field reads `Accepted` at line 5. |

## Convention Notes

None.

## Unresolved Assumptions or Follow-Up

- Existing repositories using old flat paths (`issues/`, `implementation/`, `reviews/`) must manually migrate files to the `tasks/` structure; this is explicitly out of scope per the task definition.
- Internal cross-references in previously written output files (e.g., `issue:` frontmatter pointing to `issues/001-slug.md`) will be stale until updated manually — also out of scope.
