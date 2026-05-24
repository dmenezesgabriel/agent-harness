# Implementation Summary — 039: Fix implement-it measurement gaps

## Files Changed

- `benchmarks/tasks/implement-it/001-token-bucket.json` — added `"behave"` to `evaluators`
- `benchmarks/tasks/implement-it/002-lru-cache.json` — added `"behave"` to `evaluators`
- `benchmarks/tasks/implement-it/003-event-bus.json` — added `"behave"` to `evaluators`
- `benchmarks/tasks/implement-it/004-retry-decorator.json` — added `"behave"` to `evaluators`
- `benchmarks/tasks/implement-it/005-merkle-tree.json` — added `"behave"` to `evaluators`
- `benchmarks/harness/adapters/pi_agent.py` — `output_tokens` now sums `_approx_tokens` over all `workspace_snapshot` values; falls back to `_approx_tokens(raw_output)` when snapshot is empty
- `benchmarks/tests/test_pi_agent.py` — new test file with UT-001 and IT-001

## Behavior Implemented

**FR-001 (Gap 1 — behave evaluator never runs):** All five implement-it task JSONs now declare `"evaluators": ["code", "behave"]`. The runner invokes `BehaveEvaluator` for every implement-it task, so `behave_pass_rate` reflects whether the agent wrote compliant `implementation/*.md` summaries.

**FR-002 (Gap 2 — output_tokens undercounts):** `PiAgentAdapter.run()` now computes `output_tokens` by summing `_approx_tokens(content)` over every value in `workspace_snapshot`. When the snapshot is empty the old fallback (`_approx_tokens(raw_output)`) is retained. Only `output_tokens` (and transitively `total_tokens`) change; no other `TaskResult` fields are affected.

## Tests Added

- `test_output_tokens_counts_all_snapshot_files` (UT-001): verifies the new formula produces more tokens than the old markdown-only formula when a Python file is present in the snapshot.
- `test_behave_evaluator_sets_pass_rate_for_implement_it` (IT-001): constructs a `TaskResult` with a valid `implementation/001-solution-summary.md` in the workspace snapshot, runs `BehaveEvaluator.evaluate()`, and asserts `behave_pass_rate > 0.0`.

## Validations Run

- `pytest tests/test_pi_agent.py -v` — 2 passed
- `pytest tests/ --ignore=tests/test_behave_integration.py` — 118 passed, 0 failed

## Design Notes

`output_tokens` now aggregates over `workspace_snapshot.values()` rather than the concatenated `raw_output` string. This is consistent with how `CodeEvaluator` and `BehaveEvaluator` already consume the snapshot. The fallback to `raw_output` preserves correct behavior for skills that write no files.

## ADR Updates

Not applicable — no architectural decision records were affected.
