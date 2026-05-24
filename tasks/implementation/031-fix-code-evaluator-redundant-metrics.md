---
id: "031"
issue: "tasks/issues/031-fix-code-evaluator-redundant-metrics.md"
created: 2026-05-23
updated: 2026-05-23
---

# Implementation Summary: Fix CodeEvaluator redundant precision/recall/F1 metrics

## Related Task

- `tasks/issues/031-fix-code-evaluator-redundant-metrics.md`

## Files Changed

- `benchmarks/harness/evaluators/code_evaluator.py` — removed `precision`/`recall`/`f1` assignment; added note in `evaluator_details` explaining they are not computed for code evaluation tasks
- `benchmarks/tests/test_code_evaluator.py` — new file with 7 tests covering UT-001 and UT-002

## Behavior Implemented

- `CodeEvaluator` no longer sets `precision`, `recall`, or `f1` to copies of `test_pass_rate`
- These fields remain at their `TrialResult` default of `0.0`
- `evaluator_details` includes a note: `"precision/recall/f1 are not computed for code evaluation tasks"`
- `test_pass_rate` and `accuracy` remain populated and correct

## Design Notes

- Chose Option 1 from the task (drop redundant metrics) over Option 2 (compute from `required_findings`) — simpler, more honest, and avoids scope creep
- The `runner.py` aggregation code (`_SCALAR_METRICS`, `mean_std` in `metrics.py`) already handles zero values gracefully — no changes needed
- `PlanEvaluator` continues to compute meaningful precision/recall/f1 from section-level TP/FP/FN — unchanged

## Tests Added or Updated

- `tests/test_code_evaluator.py`:
  - `test_code_evaluator_omits_redundant_metrics` (UT-001) — verifies precision/recall/f1 are 0.0 while test_pass_rate is 1.0
  - `test_code_evaluator_early_return_also_omits_metrics` — verifies error and no-code paths also leave metrics at 0.0
  - `test_integration_code_evaluator_metrics_not_redundant` (IT-001) — end-to-end evaluator run with workspace_snapshot, verifies precision/recall/f1 are 0.0 while test_pass_rate is 1.0
  - `test_mean_std_with_zero_values` (UT-002) — verifies mean_std doesn't crash on all-zero lists
  - `test_mean_std_with_empty_list` (UT-002) — verifies mean_std doesn't crash on empty lists
  - `test_mean_std_with_mixed_values` (UT-002) — verifies mean_std works with mixed zero/non-zero lists
  - `test_extract_code_blocks` — verifies code block extraction helper
  - `test_extract_code_blocks_empty` — verifies no-code text returns empty list

## Test Categories Not Applicable

- `E2E`, `Performance`, `Security`, `UX`, `Accessibility`, `Smoke`, `Regression`: Not applicable — no user journey, deploy behavior, performance impact, security surface, or UI changed

## Validation Run

```text
python3 -m pytest tests/test_code_evaluator.py -v — 7 passed
python3 -m pytest tests/ -v — 84 passed (7 new + 77 existing, no regressions)
```

## Accessibility Notes

Not applicable — this task changes only a backend-only metric computation, no frontend or UI.

## Observability Changes

- Added `"note"` key in `evaluator_details` JSON explaining that precision/recall/f1 are not computed for code evaluation tasks (OBS-001)

## ADR Updates

Not applicable — this task uses the existing `Evaluator` ABC and `TrialResult` dataclass without architectural changes.

## Unresolved Assumptions or Follow-Up

- If a future task wants to compute meaningful precision/recall for code tasks, it should define a true/false-positive model (e.g., checking `required_findings` against output). That would be Option 2 from the task.
