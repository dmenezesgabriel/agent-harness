---
id: "025"
issue: "tasks/issues/025-add-partial-impl-and-bundled-validation-antipatterns.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Add partial-implementation and bundled change-and-validation anti-patterns to SKILL.md

## Related Task

- `tasks/issues/025-add-partial-impl-and-bundled-validation-antipatterns.md`

## Overall Verdict

**Pass**

No Blocking findings. Implementation satisfies all functional requirements, non-functional requirements, and acceptance criteria.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|

None.

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | "Partial implementations" found at `skills/plan-it/SKILL.md:81` inside the "Anti-patterns to avoid" section |
| AC-002 | Pass | "Bundled change and validation" found at `skills/plan-it/SKILL.md:83` inside the "Anti-patterns to avoid" section |
| AC-003 | Pass | `diff skills/plan-it/SKILL.md .agents/skills/plan-it/SKILL.md` produced no output (exit 0) |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit | Not applicable | No executable logic; changes are pure Markdown |
| Integration | Not applicable | No system boundaries crossed |
| Smoke (SMK-001) | Present | `grep -n "Partial implementations" skills/plan-it/SKILL.md` → line 81 found |
| Smoke (SMK-002) | Present | `grep -n "Bundled change and validation" skills/plan-it/SKILL.md` → line 83 found |
| Smoke (SMK-003) | Present | `diff skills/plan-it/SKILL.md .agents/skills/plan-it/SKILL.md` → no output |
| E2E | Not applicable | No user-facing application |
| Regression | Not applicable | No prior defect being guarded |
| Performance | Not applicable | No runtime behavior |
| Security | Not applicable | No trust boundaries involved |
| Usability | Not applicable | No interactive UI |
| Observability | Not applicable | No logs, metrics, or traces involved |

## Observability Evaluation

Not applicable — no OBS requirements defined in the task.

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

None. Both new anti-patterns follow the bold-heading + prose format used by all six existing entries (`**Artificial task splitting**`, `**Cross-section duplication**`, etc.). Placement is at the end of the section, after `**Blocking-unaware ordering**`, which is consistent with append-order convention for this file.

## Unresolved Assumptions or Follow-Up

- None.
