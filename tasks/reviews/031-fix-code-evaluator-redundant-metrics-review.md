---
id: "031"
issue: "tasks/issues/031-fix-code-evaluator-redundant-metrics.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Fix CodeEvaluator redundant precision/recall/F1 metrics

## Related Task

- `tasks/issues/031-fix-code-evaluator-redundant-metrics.md`

## Overall Verdict

**Pass**

No Blocking findings.

## Findings

None.

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | CodeEvaluator no longer sets `precision`/`recall`/`f1` to `test_pass_rate`. Test `test_code_evaluator_omits_redundant_metrics` verifies fields remain at `0.0` while `test_pass_rate` is `1.0`. Early-return paths (error, no code) also leave them at `0.0`. |
| AC-002 | Pass | Precision/recall/f1 remain at `TrialResult` default of `0.0` instead of duplicating `test_pass_rate`. No rendering code in the harness would show identical columns. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `test_code_evaluator_omits_redundant_metrics` at `benchmarks/tests/test_code_evaluator.py:18` — verifies precision/recall/f1 are 0.0 while test_pass_rate is 1.0. Covers FR-001. |
| Unit (UT-002) | Present | `test_mean_std_with_zero_values`, `test_mean_std_with_empty_list`, `test_mean_std_with_mixed_values` at `benchmarks/tests/test_code_evaluator.py:119-139` — verify `mean_std()` handles zero/empty/mixed lists. Covers NFR-001. |
| Integration (IT-001) | Present | `test_integration_code_evaluator_metrics_not_redundant` at `benchmarks/tests/test_code_evaluator.py:117` — end-to-end evaluator run with workspace_snapshot and test_commands, verifies precision/recall/f1 are 0.0 while test_pass_rate is 1.0 and source is "snapshot". |
| Smoke (SMK-001) | Not applicable | No deploy behavior changed. |
| E2E (E2E-001) | Not applicable | No user journey changed. |
| Regression (REG-001) | Not applicable | No known previous defect. |
| Performance (PT-001) | Not applicable | No performance impact. |
| Security (ST-001) | Not applicable | No security impact. |
| Usability (UX-001) | Not applicable | No user-facing change. |
| Observability (OT-001) | Not applicable | No operational behavior changed. |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | If precision/recall/f1 are dropped, log a note in `evaluator_details` explaining they are not computed for code evaluation tasks. | Met | Note present at `benchmarks/harness/evaluators/code_evaluator.py:104`: `"note": "precision/recall/f1 are not computed for code evaluation tasks"`. Verified by test at `test_code_evaluator.py:62-63`. |

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

None.

## Unresolved Assumptions or Follow-Up

- None.
