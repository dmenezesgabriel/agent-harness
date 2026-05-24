---
id: "024"
issue: "tasks/issues/024-add-narrow-scope-and-system-integrity-rules.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Add narrow-scope and system-integrity rules to planning-rules.md

## Related Task

- `tasks/issues/024-add-narrow-scope-and-system-integrity-rules.md`

## Overall Verdict

**Pass**

No Blocking findings. One Non-blocking finding noted against FR-001 sub-rule coverage.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | FR-001 | Sub-rule 1 ("one cohesive concern… described in one sentence… one module boundary") is defined in prose but has no dedicated Good/Bad example pair. Sub-rules 2 and 3 each have explicit examples; sub-rule 1 is only illustrated implicitly by the Good examples showing single-sentence task descriptions. FR-001 requires "Good/Bad examples illustrating each sub-rule." | `skills/plan-it/references/planning-rules.md:36–49` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | "Narrow scope rule" present at line 36; Good example (Task 1: text edit, Task 2: benchmark) explicitly separates change and validation tasks. |
| AC-002 | Pass | "System integrity rule" present at line 52; Bad example states a task removes behavior "with the expectation that a follow-up task will replace it." |
| AC-003 | Pass | `diff skills/plan-it/references/planning-rules.md .agents/skills/plan-it/references/planning-rules.md` produces no output — files are identical. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit | Not applicable | Pure Markdown changes; no executable logic exists. |
| Integration | Not applicable | No system boundaries crossed. |
| Smoke (SMK-001) | Present | `grep -n "Narrow scope rule"` returns line 36. |
| Smoke (SMK-002) | Present | `grep -n "System integrity rule"` returns line 52. |
| Smoke (SMK-003) | Present | `diff` of source vs. installed returns empty output. |
| E2E | Not applicable | No user-facing application. |
| Regression | Not applicable | No prior defect being guarded. |
| Performance | Not applicable | No runtime behavior. |
| Security | Not applicable | No trust boundaries involved. |
| Usability | Not applicable | No interactive UI. |
| Observability | Not applicable | No logs, metrics, or traces involved. |

## Observability Evaluation

Not applicable — no OBS requirements defined in the task.

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

- `F-001` — Non-blocking — Existing sections in `planning-rules.md` each have a Good/Bad block that maps directly to their stated sub-rules (e.g., "Tracer-bullet planning" has one Good block and one Bad block, each covering the single rule stated above). The "Narrow scope rule" section states three distinct sub-rules in prose but provides only two Good bullets and two Bad bullets, all addressing sub-rules 2 and 3. Adding a dedicated Good/Bad pair for sub-rule 1 would bring the section into full alignment with FR-001 and with the convention of example-per-sub-rule used elsewhere.

## Unresolved Assumptions or Follow-Up

- None. All ACs, smoke tests, and Definition of Done criteria verified against actual file content and diff output.
