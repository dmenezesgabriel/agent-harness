---
task: "035"
status: completed
date: 2026-05-23
---

# Implementation: Replace trial-centric models with TaskResult and RunSummary

## Files changed

### Deleted
- `benchmarks/harness/analysis.py` — FR-004: TrialStats, analyze_trials, Wilcoxon, Cohen's d removed
- `benchmarks/tests/test_analysis.py` — FR-008: module no longer exists

### Modified — core models
- `benchmarks/harness/models.py` — FR-001/002/003: `TrialResult` → `TaskResult` (removed `condition`, `trial_index`); `ExperimentSummary` → `RunSummary` (removed `without_skill`, `p_values`, `effect_sizes`, `trial_stats`, `n_trials`; renamed `with_skill` → `metrics`); `Condition` enum deleted

### Modified — adapters
- `benchmarks/harness/adapters/base.py` — FR-005: `run(task, condition, trial_index) -> TrialResult` → `run(task) -> TaskResult`
- `benchmarks/harness/adapters/claude_code.py` — FR-005/007: removed condition branching, always uses skill, returns `TaskResult`
- `benchmarks/harness/adapters/opencode.py` — FR-005/007: same
- `benchmarks/harness/adapters/pi_agent.py` — FR-005/007: same

### Modified — tracking
- `benchmarks/harness/tracking/base.py` — FR-006: `log_trial` → `log_result`; `log_summary` accepts `RunSummary`
- `benchmarks/harness/tracking/null_tracker.py` — FR-007: updated method name and types
- `benchmarks/harness/tracking/tracker.py` — FR-007/OBS-001/002: `log_result` run name is `{task_id}`; `log_summary` writes `metrics__*` keys

### Modified — runner and CLI
- `benchmarks/harness/runner.py` — drops paired loop, produces `RunSummary`
- `benchmarks/run.py` — imports `RunSummary`, updated `_print_summary` to single-metric table

### Modified — evaluators (cascade from TrialResult → TaskResult)
- `benchmarks/harness/evaluators/base.py`
- `benchmarks/harness/evaluators/code_evaluator.py`
- `benchmarks/harness/evaluators/behave_evaluator.py`
- `benchmarks/harness/evaluators/plan_evaluator.py`
- `benchmarks/harness/evaluators/llm_judge.py`

### Modified — tests
- `benchmarks/tests/test_tracker.py` — updated fixtures, added UT-001/002/003 (035), IT-001/002 (035), OT-001 (035)
- `benchmarks/tests/test_opencode.py` — removed `Condition` from `_parse_output`/`run` calls
- `benchmarks/tests/test_plan_evaluator.py` — `TrialResult` → `TaskResult`, removed `condition`/`trial_index`
- `benchmarks/tests/test_code_evaluator.py` — same
- `benchmarks/tests/test_workspace.py` — `adapter.run(task)` with no condition/trial_index
- `benchmarks/tests/test_registry.py` — updated fake adapter signature and `TaskResult` fixture

### Modified — documentation
- `CONTEXT.md` — updated domain terms: Trial/Condition/Experiment → TaskResult/RunSummary/single-execution model

## Behavior implemented

- `TaskResult` constructs without `condition` or `trial_index`; `total_tokens` returns `input_tokens + output_tokens`
- `RunSummary` has `metrics` dict; `without_skill`, `p_values`, `effect_sizes`, `trial_stats`, `n_trials` are absent
- All adapters call `adapter.run(task)` with no condition argument; always use the skill
- `NullTracker.log_result` and `MLflowTracker.log_result` implement the new method name
- `MLflowTracker.log_result` run name is `{task_id}` (no condition/trial suffix)
- `MLflowTracker.log_summary` writes `metrics__{name}__mean` and `metrics__{name}__std` keys

## Tests added / updated

- **UT-001 (035)**: `TaskResult.total_tokens` returns `input_tokens + output_tokens`
- **UT-002 (035)**: `RunSummary` field access — expected fields present, old ones absent
- **UT-003 (035)**: `GoldStandard` default fields unchanged
- **IT-001 (035)**: `ClaudeCodeAdapter.run(task)` returns `TaskResult` (covered by existing workspace test)
- **IT-002 (035)**: `NullTracker.log_result` returns `""` and writes warning to stderr
- **OT-001 (035)**: `MLflowTracker.log_result` run name equals `task_id`

## Validation

- 100 tests pass, 5 warnings (MLflow FutureWarning about file backend — pre-existing, out of scope)

## Accessibility

Not applicable — no UI touched.

## ADRs updated

None — ADR 003 was already accepted as a precondition for this task.

## Intentional non-applicable test categories

- Smoke, E2E, regression, performance, security, usability: per task spec, no startup path, user-facing behavior, or security boundary changed.

## Unresolved assumptions / follow-up

- `champion.py` and `test_champion.py` still reference `with_skill__*` metric keys from MLflow — these are read from historical runs and belong to a separate task (CLI updates, likely 038).
- The `n_trials` parameter is still accepted by `BenchmarkRunner.run_experiment()` and `run_experiment()` signatures for API compatibility but is now ignored internally.
