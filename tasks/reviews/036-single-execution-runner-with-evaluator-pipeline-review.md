---
id: "036"
review_date: 2026-05-23
verdict: Pass
blocking_count: 0
non_blocking_count: 1
suggestion_count: 0
---

# Review: 036 — Single-execution runner with task-declared evaluator pipeline

## Verdict

**Pass** — 0 Blocking findings. Implementation satisfies all FRs, NFRs, and ACs. All 6 required tests present and green. Full suite at 106 passed.

---

## Acceptance Criteria

| AC | Description | Result | Notes |
|----|-------------|--------|-------|
| AC-001 | `plan` evaluator called before `behave` on same `TaskResult` | ✅ Pass | `test_runner_applies_evaluators_in_declared_order` records `call_order` list; asserts `["plan", "behave"]` |
| AC-002 | `behave` evaluator NOT called for `evaluators: ["code"]` task | ✅ Pass | `test_runner_skips_behave_for_code_only_task` asserts `behave_ev.evaluate.assert_not_called()` |
| AC-003 | `Task.from_dict` without `"evaluators"` key → `[task.evaluator]` | ✅ Pass | `test_task_from_dict_no_evaluators_key_falls_back_to_evaluator` in `test_tracker.py` |
| AC-004 | Calling `run_experiment()` with `n_trials`, `use_judge`, or `with_skill_only` raises `TypeError` | ✅ Pass | Verified by signature inspection; parameters absent from both `run_experiment()` and `BenchmarkRunner.run_experiment()`. No dedicated test required per issue's Required Tests section. |
| AC-005 | `PlanEvaluator.evaluate()` leaves `precision`, `recall`, `f1` at `0.0` | ✅ Pass | `test_plan_evaluator_does_not_set_precision_recall_f1` asserts all three are `0.0`; evaluator code confirms neither field is written |
| AC-006 | Plan-it corpus tasks load with `evaluators == ["plan", "behave"]` | ✅ Pass | All 5 plan-it JSONs (`001`–`005`) confirmed to have `"evaluators": ["plan", "behave"]` |

---

## Functional Requirements

| FR | Description | Result |
|----|-------------|--------|
| FR-001 | Each task executed exactly once (no N-trial loop, no `n_trials` param) | ✅ Pass — `runner.py` has a flat `for task in tasks:` loop; no nesting or repeat calls |
| FR-002 | `WITHOUT_SKILL` branch and `without_skill` aggregation removed | ✅ Pass — no such references in `runner.py` |
| FR-003 | Hardcoded `behave_ev` crosscutting call removed | ✅ Pass — grep confirms absent |
| FR-004 | Runner applies `task.evaluators` in declaration order | ✅ Pass — `runner.py:80–82` iterates `for ev_name in task.evaluators:` without reordering |
| FR-005 | `Task.evaluators: list[str]`; `from_dict` defaults to `[task.evaluator]` | ✅ Pass — `models.py:35,58` |
| FR-006 | All plan-it corpus files include `["plan","behave"]`; all implement-it include `["code"]` | ✅ Pass — 5+5 files verified |
| FR-007 | `run_experiment()` removes `n_trials`, `use_judge`, `with_skill_only` | ✅ Pass — signature is `(adapter, skill, tasks_dir, tracker, task_ids, skill_dir)` |
| FR-008 | `LLMJudge` removed from runner import and core loop; module retained as standalone | ✅ Pass — `llm_judge.py` exists; grep on `runner.py` finds no reference |
| FR-009 | `PlanEvaluator.evaluate()` stops computing `precision`, `recall`, `f1` | ✅ Pass — none of the three fields are written in `plan_evaluator.py` |

---

## Non-Functional Requirements

| NFR | Description | Result |
|-----|-------------|--------|
| NFR-001 | `runner.py` does not import or reference `Condition`, `TrialStats`, or `analyze_trials` | ✅ Pass — confirmed by grep |
| NFR-002 | Evaluator order matches `task.evaluators` declaration order; no implicit reordering | ✅ Pass — Python list iteration preserves order; verified by IT-001 |
| NFR-003 | Adding a new evaluator does not require modifying the runner | ✅ Pass — runner resolves only from registry; the pipeline loop is fully data-driven |

---

## Observability Requirements

Not applicable — no new telemetry introduced in this task.

---

## Test Coverage

| Test ID | Name | File | Requirement | Result |
|---------|------|------|-------------|--------|
| UT-001 | `test_task_from_dict_no_evaluators_key_falls_back_to_evaluator` | `test_tracker.py` | FR-005, AC-003 | ✅ Present, green |
| UT-002 | `test_task_from_dict_with_explicit_evaluators_key` | `test_tracker.py` | FR-005 | ✅ Present, green |
| UT-003 | `test_plan_evaluator_does_not_set_precision_recall_f1` | `test_plan_evaluator.py` | FR-009, AC-005 | ✅ Present, green |
| IT-001 | `test_runner_applies_evaluators_in_declared_order` | `test_registry.py` | FR-004, AC-001 | ✅ Present, green |
| IT-002 | `test_runner_skips_behave_for_code_only_task` | `test_registry.py` | FR-003, AC-002 | ✅ Present, green |
| IT-003 | `test_benchmark_runner_returns_run_summary_single_execution` | `test_tracker.py` | FR-001, FR-007 | ✅ Present, green |

Updated tests (existing tests adjusted to remove removed parameters):

- `test_benchmark_runner_with_null_tracker` (`test_tracker.py`) — calls `run_experiment()` without removed parameters ✅
- `test_runner_resolves_evaluator_through_registry` (`test_registry.py`) — task JSON now includes `"evaluators"` field ✅

**Full suite: 106 passed, 0 failed.**

---

## ADR Compliance

The implementation summary notes this task follows ADR 003 (`docs/adrs/003-drop-paired-experiment-model.md`) without new decisions. No new ADRs were required or opened. Task DoD is silent on ADR updates. Not a finding.

---

## Findings

### Non-blocking

**NB-001**: `run.py` retains `--judge/--no-judge` CLI option as dead code.

- **Location**: `benchmarks/run.py:101,110,134`
- **Detail**: The `judge: bool` parameter is accepted by the `main()` click command and printed in the console preamble (`"LLM judge: disabled"`), but is never passed to `run_experiment()` or used anywhere in the call path. A user who passes `--judge` will see no effect and no warning.
- **Why Non-blocking**: FR-008 only requires removing `LLMJudge` from `runner.py`'s import and core loop — both satisfied. The task DoD does not mention the CLI flag. The implementation summary explicitly documents this as intentionally deferred to task 038 (CLI alignment). No FR or AC is violated.
- **Recommendation**: Task 038 should remove the `--judge/--no-judge` option from `run.py` and its associated preamble print statement to avoid misleading users.

---

## Summary

The implementation is complete and correct. All 9 FRs, 3 NFRs, and 6 ACs pass. All 6 required tests are present and green. The one non-blocking finding (`run.py` judge dead code) is already tracked for cleanup in task 038 and does not affect any runner contract. Ready to close task 036.
