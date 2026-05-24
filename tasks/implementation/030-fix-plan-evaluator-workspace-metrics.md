# Implementation Summary: Fix PlanEvaluator workspace metrics

**Task**: `030-fix-plan-evaluator-workspace-metrics.md`

## Files changed

- `benchmarks/harness/evaluators/plan_evaluator.py` — core fixes
- `benchmarks/tests/test_plan_evaluator.py` — new test suite (77 tests total, all pass)

## Behavior implemented

- **FR-001 / FR-004**: `_merge_content()` combines `raw_output` + `workspace_snapshot` into a single text before evaluation. Both section detection and classification checks now see content from all sources.
- **FR-002**: `_score_completeness()` computes `fp` as the count of present markdown headings that don't match any required section, replacing the hardcoded `fp=0`. Precision now correctly reflects extra/hallucinated sections.
- **FR-003**: `_has_classification()` already handled case-insensitive matching via `.lower()`. No code change needed — confirmed by `UT-003` parametrized tests.
- **NFR-001**: Existing gold standards unchanged, same `required_sections` format.
- **NFR-002**: Empty/absent `workspace_snapshot` falls back to `raw_output` only; empty both returns zero metrics without crashing.
- **OBS-001**: `evaluator_details["content_source"]` logs `"raw_output"`, `"workspace_snapshot"`, `"both"`, or `"none"`.
- **OBS-002**: `evaluator_details["sections_extra"]` logs the false-positive (extra section) count.
- **Edge case**: `result.error` short-circuits early before any merge attempt.

## Tests added

| ID | Description | Status |
|---|---|---|
| `UT-001` | Merge `raw_output` + `workspace_snapshot`, verify sections found from both | ✅ |
| `UT-002` | Compute precision with known false positives, verify `fp > 0` and `precision < 1.0` | ✅ |
| `UT-003` | Parametrized case variants for AFK/HITL classification | ✅ |
| `IT-001` | End-to-end: PlanEvaluator with file-writing agent (workspace files only) | ✅ |
| — | Fallback to `raw_output` when `workspace_snapshot` is empty | ✅ |
| — | No crash when both sources empty | ✅ |
| — | Error state returns zero metrics | ✅ |
| — | Precision reflects false positives via `evaluate()` | ✅ |

## Validations run

- All 77 tests pass (74 existing + 11 new, including parametrized variants)
- No pre-existing failures

## Test categories not applicable

- `SMK-001` — no deploy availability change
- `E2E-001` — no user journey changed
- `REG-001` — no known previous defect
- `PT-001` — no performance impact
- `ST-001` — no auth/security touch
- `UX-001` — no user-facing change
- `OT-002` — only logging changes (already covered by OBS tests)

## Unresolved assumptions

- The `bench-run` CLI producing non-zero accuracy for plan-it tasks on OpenCode with deepseek (DoD item) cannot be verified without a real model run; rely on the unit/integration test coverage.
