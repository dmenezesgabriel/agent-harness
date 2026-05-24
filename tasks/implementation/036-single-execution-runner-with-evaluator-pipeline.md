# Implementation: 036 — Single-execution runner with task-declared evaluator pipeline

## Files changed

- `benchmarks/harness/models.py` — Added `evaluators: list[str]` field to `Task`; `from_dict()` defaults to `[evaluator]` when key absent
- `benchmarks/harness/runner.py` — Removed `LLMJudge` import, `n_trials`/`use_judge`/`with_skill_only` parameters, hardcoded `behave_ev` call; replaced single-evaluator dispatch with pipeline loop over `task.evaluators`
- `benchmarks/harness/evaluators/plan_evaluator.py` — Removed `precision`/`recall`/`f1` computation; `completeness_score` now uses `result.accuracy` (equivalent value); import cleaned up
- `benchmarks/run.py` — Removed `use_judge=judge` from `run_experiment()` call
- `benchmarks/tasks/plan-it/{001–005}.json` — Added `"evaluators": ["plan", "behave"]`
- `benchmarks/tasks/implement-it/{001–005}.json` — Added `"evaluators": ["code"]`
- `benchmarks/tests/test_plan_evaluator.py` — Updated IT-001 and `test_evaluate_precision_reflects_false_positives` assertions from non-zero to `0.0`; added UT-003
- `benchmarks/tests/test_registry.py` — Updated IT-001 (removed deleted params, changed task JSON to include `evaluators`); added IT-001 (036) ordering test and IT-002 behave-skip test
- `benchmarks/tests/test_tracker.py` — Added UT-001, UT-002 for `Task.from_dict`; added IT-003 single-execution assertion

## Behavior implemented

- Each task runs exactly once; the runner applies `task.evaluators` in declaration order via `evaluator_registry.resolve()`
- No crosscutting behave call: behave is invoked only when `"behave"` appears in `task.evaluators`
- `BenchmarkRunner.run_experiment()` signature: `(adapter, skill, tasks_dir, task_ids=None, skill_dir=None)` — no `n_trials`, `use_judge`, `with_skill_only`
- `Task.from_dict` backward-compatible: missing `"evaluators"` key falls back to `[task.evaluator]`
- `PlanEvaluator` leaves `precision`, `recall`, `f1` at `0.0`; retains `accuracy` and `quality_score`

## Tests added or updated

- **UT-001**: `Task.from_dict` with no `evaluators` key defaults to `[evaluator]`
- **UT-002**: `Task.from_dict` with explicit `evaluators` key parses correctly
- **UT-003**: `PlanEvaluator.evaluate()` leaves `precision`/`recall`/`f1` at `0.0`
- **IT-001 (036)**: Runner calls evaluators in declared order (`plan` before `behave`)
- **IT-002 (036)**: Runner never calls `behave.evaluate` when `task.evaluators == ["code"]`
- **IT-003 (036)**: `BenchmarkRunner` with `NullTracker` returns `RunSummary` with `n_tasks == 1`
- Updated existing IT-001 tests in `test_registry.py` and `test_tracker.py` to drop removed parameters

## Validations run

- `106 passed` — full test suite green
- No disabled tests, no `--force` flags

## Accessibility checks

Not applicable — no UI touched.

## ADRs updated

None — implementation follows ADR 003 (drop paired experiment model) without new decisions.

## Intentional non-applicable test categories

- Smoke, E2E, regression, performance, security, usability, observability — as specified in the task definition.

## Unresolved assumptions

- `run.py` still defines `--judge/--no-judge` CLI option (now a no-op); task 038 will remove it.
- `LLMJudge` module retained at `harness/evaluators/llm_judge.py` as standalone callable per FR-008.
