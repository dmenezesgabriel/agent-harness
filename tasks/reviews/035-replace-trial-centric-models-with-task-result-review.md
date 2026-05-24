---
id: "035"
issue: "tasks/issues/035-replace-trial-centric-models-with-task-result.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Replace trial-centric models with TaskResult and RunSummary

## Related Task

- `tasks/issues/035-replace-trial-centric-models-with-task-result.md`

## Overall Verdict

**Pass**

No Blocking findings. One Non-blocking finding (IT-001 partial test coverage) and two Suggestions (dead runner parameters, stale champion metric keys). Safe to mark complete.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | IT-001 | The workspace test used to satisfy IT-001 (`test_claude_code_adapter_delegates_workspace_lifecycle`) does not assert all fields specified by the scenario: `isinstance(result, TaskResult)`, `result.task_id`, `result.skill`, `result.platform`, `result.latency_ms > 0` are unchecked. The test only asserts `result.error == ""`. The adapter code is correct, but the test does not fully verify the IT-001 postconditions. | `benchmarks/tests/test_workspace.py:127-149` |
| F-002 | Suggestion | — | `n_trials` and `with_skill_only` parameters remain in both `run_experiment()` and `BenchmarkRunner.run_experiment()` signatures and are accepted but never used internally. The implementation summary acknowledges this as a deliberate compatibility hold. Dead parameters risk misleading callers who pass `n_trials > 1` expecting multiple executions. | `benchmarks/harness/runner.py:55,59,132,136` |
| F-003 | Suggestion | — | `champion.py` still reads `with_skill__behave_pass_rate__mean`, `with_skill__f1__mean`, `with_skill__quality_score__mean`, `with_skill__latency_ms__mean` metric keys from MLflow. These keys no longer exist under the `metrics__*__mean` naming introduced by OBS-002. The implementation summary correctly scopes this to task 038. | `benchmarks/champion.py:114-117` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `TaskResult` has no `condition` or `trial_index` fields; `total_tokens` property returns `input_tokens + output_tokens`. Verified at `benchmarks/harness/models.py:84-86`. |
| AC-002 | Pass | `RunSummary` has `metrics: dict[str, tuple[float, float]]`; `summary.metrics["accuracy"]` returns the stored tuple. Verified at `benchmarks/harness/models.py:89-96`. |
| AC-003 | Pass | All three adapters (`ClaudeCodeAdapter`, `OpenCodeAdapter`, `PiAgentAdapter`) implement `run(self, task: Task) -> TaskResult` with no `condition` or `trial_index`. Verified in `adapters/claude_code.py:58`, `adapters/opencode.py:44`, `adapters/pi_agent.py:81`. |
| AC-004 | Pass | `NullTracker.log_result(result, task)` returns `""` without raising. Verified at `benchmarks/harness/tracking/null_tracker.py:21`. |
| AC-005 | Pass | `MLflowTracker.log_result` calls `mlflow.start_run(run_name=result.task_id)` — no condition or trial suffix. Verified at `benchmarks/harness/tracking/tracker.py:38`; asserted by OT-001 test. |
| AC-006 | Pass | `grep -rn "TrialResult\|ExperimentSummary\|Condition\|trial_index" benchmarks/tests/` returned no matches (one docstring comment "no condition or trial suffix" is expected English prose, not a type reference). |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `test_task_result_total_tokens` in `benchmarks/tests/test_tracker.py:60-70` |
| Unit (UT-002) | Present | `test_run_summary_field_access` in `benchmarks/tests/test_tracker.py:77-92`; asserts `metrics` present and `without_skill`, `p_values`, `trial_stats`, `n_trials` absent |
| Unit (UT-003) | Present | `test_gold_standard_defaults` in `benchmarks/tests/test_tracker.py:98-103` |
| Integration (IT-001) | Present (partial) | `test_claude_code_adapter_delegates_workspace_lifecycle` in `benchmarks/tests/test_workspace.py:127-149` covers the adapter run path with no condition/trial_index, but does not assert all IT-001 postconditions (task_id, skill, platform, latency_ms). See F-001. |
| Integration (IT-002) | Present | `test_null_tracker_log_result_returns_empty_string` in `benchmarks/tests/test_tracker.py:208-213`; verifies return `""` and warning in stderr. Note: the warning originates from `NullTracker.__init__`, not from `log_result` itself — capsys captures both. |
| Smoke | Not applicable | No deploy or startup path changed. |
| E2E | Not applicable | No user-facing behavior changed. |
| Regression | Not applicable | No previously broken defect being fixed. |
| Performance | Not applicable | No performance-sensitive path changed. |
| Security | Not applicable | No auth or trust boundary changed. |
| Usability | Not applicable | CLI updated in task 038. |
| Observability (OT-001) | Present | `test_mlflow_tracker_log_result_run_name_is_task_id` in `benchmarks/tests/test_tracker.py:230-248`; asserts `mock_start_run.assert_called_once_with(run_name=result.task_id)`. |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | `MLflowTracker.log_result()` run name is `{task_id}` | Met | `mlflow.start_run(run_name=result.task_id)` at `benchmarks/harness/tracking/tracker.py:38`. OT-001 verifies this assertion. |
| OBS-002 | `log_summary()` drops old `without_skill__*`/`p_value__*`/`effect_size__*` keys; writes `metrics__*` keys | Met | `tracker.py:98-100` iterates `summary.metrics.items()` and writes `f"metrics__{metric_name}__mean"` and `f"metrics__{metric_name}__std"`. No old keys present. |

## ADR Compliance

| ADR | Required Action | Status |
|-----|-----------------|--------|
| `docs/adrs/003-drop-paired-experiment-model.md` | Precondition — must be Accepted before this task starts | Done — status is `Accepted` (verified in frontmatter). No update required by this task's DoD. |

## Convention Notes

- `F-002` — Suggestion — Dead `n_trials` and `with_skill_only` parameters in `runner.py` are an inherited signature from the pre-035 design. The implementation summary notes them as a known gap for a follow-up task. No convention violation, but the pattern of silently ignoring named parameters is unusual for this codebase.
- `F-003` — Suggestion — `champion.py` references `with_skill__*` MLflow metric keys that were renamed by OBS-002. This is a known cross-task inconsistency scoped to task 038 per the implementation summary. No action needed in task 035.

## Unresolved Assumptions or Follow-Up

- IT-001 test coverage is partial (F-001). Adding assertions for `result.task_id`, `result.skill`, `result.platform`, and `result.latency_ms > 0` to `test_claude_code_adapter_delegates_workspace_lifecycle` would fully satisfy the IT-001 spec — recommend addressing in a follow-up or during task 038 test sweep.
- `n_trials` and `with_skill_only` dead parameters in `runner.py` (F-002) are deferred to a later task. Recommend removing them alongside the CLI update in task 038 to avoid user confusion.
- `champion.py` `with_skill__*` metric key reads (F-003) are acknowledged as out of scope; tracked for task 038.
