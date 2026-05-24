---
id: "040"
created: 2026-05-24
updated: 2026-05-24
status: active
---

# Task: Wire LLM judge as a registered evaluator

## Priority

P1 — `judge_score` is always `0.0` for all skills. `LLMJudge` exists but is not connected to the evaluator pipeline, so plan-it has no pointwise quality signal beyond the heuristic `quality_score`.

## Dependencies

- No task dependency; can start independently.
- No ADR dependency; the Evaluator extension pattern is established in `docs/adrs/002-extension-point-interface-mechanism.md` — this task follows it.

## Assignability

**AFK** — The Evaluator interface, registry registration pattern, and LLMJudge implementation are all in place. The missing piece is a thin adapter class and two registration/config changes that are fully specified here.

## Context

`LLMJudge` in `harness/evaluators/llm_judge.py` provides a `pointwise(result, task_title, instruction)` method that calls `claude-haiku-4-5-20251001` and returns a `(score_0_to_10, reason)` tuple. It is not a subclass of `Evaluator` and is not registered in `evaluator_registry`. As a result:

- `"llm_judge"` cannot appear in any task's `evaluators` list without raising a `KeyError`.
- `judge_score` is always the `TaskResult` field default (`0.0`).
- plan-it has no judge signal despite its outputs being a natural fit for pointwise LLM scoring (structured text is harder to evaluate heuristically than code pass/fail tests).

The fix is three steps:
1. Add `LLMJudgeEvaluator(Evaluator)` to `llm_judge.py` — wraps `LLMJudge.pointwise()` and writes `result.judge_score`.
2. Register `"llm_judge"` → `LLMJudgeEvaluator` in `harness/evaluators/__init__.py`.
3. Add `"llm_judge"` to each plan-it task's `evaluators` list.

implement-it tasks are excluded: code test pass/fail is already an objective, unambiguous signal. Adding a judge there adds cost without proportionate benefit.

## Use Cases

- **Feature**: plan-it benchmarking
- **Scenario**: LLM judge scores a plan-it output
- **Given** a plan-it benchmark run completes
- **When** results are aggregated
- **Then** `judge_score` is a non-zero value reflecting plan quality as assessed by the judge model

- **Scenario**: Judge evaluator is optional per task
- **Given** an implement-it task with `"evaluators": ["code", "behave"]`
- **When** the runner processes that task
- **Then** `LLMJudgeEvaluator` is not called and `judge_score` remains `0.0`

## Definition of Ready

- `LLMJudge.pointwise()` exists and returns `(float, str)` (confirmed).
- `Evaluator` ABC requires only `evaluate(self, result: TaskResult, task: Task) -> TaskResult` (confirmed).
- `evaluator_registry.register(name, cls)` pattern is established (confirmed: `behave`, `code`, `plan` are registered this way).
- `TaskResult.judge_score` field exists as a `float` default `0.0` (confirm in `harness/models.py` before implementing).

## Functional Requirements

- `FR-001`: A `LLMJudgeEvaluator` class in `harness/evaluators/llm_judge.py` must subclass `Evaluator`, implement `evaluate(self, result, task) -> TaskResult`, call `LLMJudge().pointwise(result, task.title, task.instruction)`, and write the returned score to `result.judge_score`.
- `FR-002`: `harness/evaluators/__init__.py` must register `LLMJudgeEvaluator` under the name `"llm_judge"` using `evaluator_registry.register`.
- `FR-003`: All five plan-it task JSON files must include `"llm_judge"` in their `evaluators` list (after `"plan"` and `"behave"`).
- `FR-004`: When `LLMJudge.pointwise()` raises an exception, `LLMJudgeEvaluator.evaluate()` must catch it, set `result.judge_score = 0.0`, and record the error in `result.evaluator_details` without re-raising.

## Non-Functional Requirements

- `NFR-001`: `LLMJudgeEvaluator` must not mutate any `TaskResult` field other than `judge_score` and `evaluator_details`.
- `NFR-002`: The judge model call must use at most 256 output tokens (already enforced in `LLMJudge.pointwise()` via `max_tokens=256`).

## Observability Requirements

- `OBS-001`: Not applicable — harness has no production telemetry; `judge_score` is logged to MLflow via the existing `Tracker`.

## Acceptance Criteria

- `AC-001`: **Given** a plan-it benchmark run over 5 tasks, **When** results are printed, **Then** `judge_score` mean is greater than `0.0`.
- `AC-002`: **Given** `LLMJudge.pointwise()` raises an `anthropic.APIError`, **When** `LLMJudgeEvaluator.evaluate()` is called, **Then** `result.judge_score == 0.0` and `result.evaluator_details` contains a `"judge_error"` key.
- `AC-003`: **Given** an implement-it task with `"evaluators": ["code", "behave"]`, **When** the runner processes it, **Then** `LLMJudgeEvaluator.evaluate()` is never called (no judge API call is made).

## Required Tests

### Unit Tests

- `UT-001`: Mock `LLMJudge.pointwise()` to return `(8.5, "Good plan")`. Call `LLMJudgeEvaluator.evaluate(result, task)`. Assert `result.judge_score == 8.5`. Covers `FR-001`.
- `UT-002`: Mock `LLMJudge.pointwise()` to raise `Exception("api error")`. Assert `result.judge_score == 0.0` and `"judge_error"` in `result.evaluator_details`. Covers `FR-004`, `AC-002`.
- `UT-003`: Assert `evaluator_registry.resolve("llm_judge")` returns an instance of `LLMJudgeEvaluator` (or its class). Covers `FR-002`.

### Integration Tests

- `IT-001`: **Scenario**: judge_score is non-zero after a plan-it run  
  **Given** a plan-it benchmark run with one task and `evaluators: ["plan", "behave", "llm_judge"]`  
  **When** the evaluator pipeline runs against a non-empty `TaskResult`  
  **Then** `result.judge_score > 0.0`  
  Covers `FR-001`, `FR-002`, `AC-001`.

### Smoke Tests

Not applicable — no deployment path.

### End-to-End Tests

Not applicable — covered by integration test above.

### Regression Tests

Not applicable — no previous defect.

### Performance Tests

Not applicable — judge latency is bounded by the haiku API call; no harness-side constraint.

### Security Tests

Not applicable — judge only reads `TaskResult` fields; no user-controlled input reaches the judge prompt unsanitized (task title and instruction are corpus-controlled).

### Usability Tests

Not applicable — CLI tool, no UI.

### Observability Tests

Not applicable — `OBS-001` is not applicable.

## Definition of Done

- `LLMJudgeEvaluator` is implemented and registered.
- All five plan-it task JSONs include `"llm_judge"` in `evaluators`.
- `UT-001`, `UT-002`, `UT-003`, and `IT-001` pass.
- A benchmark re-run shows `judge_score` mean is greater than `0.0` for plan-it.
- implement-it `judge_score` remains `0.0` (judge not called).
