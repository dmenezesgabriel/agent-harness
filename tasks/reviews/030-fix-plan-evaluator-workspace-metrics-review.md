---
id: "030"
issue: "tasks/issues/030-fix-plan-evaluator-workspace-metrics.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Fix PlanEvaluator workspace metrics

## Related Task

- `tasks/issues/030-fix-plan-evaluator-workspace-metrics.md`

## Overall Verdict

**Pass**

No Blocking findings.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Suggestion | — | `_merge_content()` prefixes workspace file content with `# File: {path}`, which creates a markdown heading not in any required section. This inflates `fp` counts by one per workspace file. Consider using an HTML comment prefix instead, or filter these synthetic headings out in `_all_present_sections()`. | `benchmarks/harness/evaluators/plan_evaluator.py:92` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | Test `test_evaluate_finds_sections_in_workspace_files()` verifies `accuracy > 0.0` when sections exist only in workspace files with empty `raw_output`. |
| AC-002 | Pass | Test `test_evaluate_precision_reflects_false_positives()` verifies `sections_extra > 0` and `precision < 1.0` when extra sections are present. |
| AC-003 | Pass | Test `test_evaluate_falls_back_to_raw_output_when_no_workspace()` verifies fallback with `content_source == "raw_output"` and `accuracy > 0.0`. Test `test_evaluate_no_crash_on_empty_both()` verifies no crash when both sources are empty. |
| AC-004 | Pass | Test `test_has_classification_afk_uppercase()` verifies `_has_classification()` returns `True` for `"## HITL Decision Point"`. Parametrized test `test_classification_matches_case_variants` covers all six case variants. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `test_merge_sections_from_both_sources()` and `test_merge_sections_workspace_only()` verify merge and section detection from both sources. |
| Unit (UT-002) | Present | `test_precision_drops_with_extra_sections()` and `test_no_extra_sections_precision_one()` verify `fp > 0` and `precision < 1.0`. |
| Unit (UT-003) | Present | `test_classification_matches_case_variants()` parametrized for AFK, afk, Afk, HITL, hitl, Hitl — all return `True`. |
| Integration (IT-001) | Present | `test_evaluate_finds_sections_in_workspace_files()` end-to-end test with file-writing agent, empty `raw_output`, sections in workspace. |
| Smoke (SMK-001) | Not applicable | No deploy availability change. |
| E2E (E2E-001) | Not applicable | No user journey changed. |
| Regression (REG-001) | Not applicable | No known previous defect. |
| Performance (PT-001) | Not applicable | No performance impact. |
| Security (ST-001) | Not applicable | No auth/security touch. |
| Usability (UX-001) | Not applicable | No user-facing change. |
| Observability (OT-002) | Not applicable | Already covered by OBS tests. |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | Log content source in `evaluator_details` | Met | `evaluator_details["content_source"]` at `plan_evaluator.py:165` — set to `"raw_output"`, `"workspace_snapshot"`, `"both"`, or `"none"`. |
| OBS-002 | Log false-positive section count in `evaluator_details` | Met | `evaluator_details["sections_extra"]` at `plan_evaluator.py:168` — set to `fp` from `_score_completeness()`. |

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

- F-001 — Suggestion — `_merge_content()` uses `# File: {path}` to delimit workspace files in merged text. This creates synthetic markdown headings that are never in `required_sections`, inflating `fp`. Consider using an HTML comment prefix or filtering in `_all_present_sections()`.

## Unresolved Assumptions or Follow-Up

- The DoD item "bench-run CLI produces non-zero accuracy for plan-it tasks on OpenCode with deepseek" cannot be verified without a real model run. Unit and integration test coverage provides reasonable confidence.
