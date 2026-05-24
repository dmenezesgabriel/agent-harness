---
id: "031"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Fix CodeEvaluator redundant precision/recall/F1 metrics

## Priority

P0 — Precision, recall, and F1 are reported as independent metrics but are all identical copies of `test_pass_rate`. This is misleading and devalues the benchmark report.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this task uses the existing `Evaluator` ABC and `TrialResult`.

## Assignability

**AFK** — all requirements and acceptance criteria are resolved; no decisions remain open.

## Context

The `CodeEvaluator` (`benchmarks/harness/evaluators/code_evaluator.py`) sets:

```python
result.test_pass_rate = rate
result.accuracy = 1.0 if rate == 1.0 else rate
result.precision = rate
result.recall = rate
result.f1 = rate
```

All three of precision, recall, and F1 are identical copies of `test_pass_rate`. A reader comparing these columns in the benchmark report sees the same number three times and learns nothing.

The root cause: for a code-evaluation task, the concepts of true/false positives and negatives map poorly onto test pass/fail results. The correct approach is to either:
1. Drop the redundant metrics and rely solely on `test_pass_rate` and `accuracy`, or
2. Define non-trivial precision/recall that measure something different (e.g., precision = fraction of output code that is functionally relevant, recall = fraction of required behaviors covered).

Option 1 is simpler and more honest. Option 2 requires a deeper change (e.g., checking gold standard required_findings against output).

## Use Cases

- **Feature**: Benchmark report interpretation
- **Scenario**: Researcher reads a benchmark results table
- **Given** the report shows Precision: 1.000, Recall: 1.000, F1: 1.000, and Test Pass Rate: 1.000
- **When** the researcher examines the evaluator
- **Then** they find all three metrics are derived from the same single number

## Definition of Ready

- The current metric computation code in `code_evaluator.py` is understood.
- The `TrialResult` dataclass fields for precision, recall, f1 are not used elsewhere in a way that would break.

## Functional Requirements

- `FR-001`: `CodeEvaluator` must not set `precision`, `recall`, and `f1` to copies of `test_pass_rate`.
- `FR-002`: Either drop precision/recall/f1 from code-evaluated trials entirely, or compute them from a distinct signal (e.g., proportion of `required_findings` present in output).
- `FR-003`: The `test_pass_rate` and `accuracy` fields must remain populated and correct.

## Non-Functional Requirements

- `NFR-001`: The change must not break the `ExperimentSummary` aggregation code, which groups all metrics by name across tasks.
- `NFR-002`: The `bench-run` CLI output must not show duplicate values for different metric names.

## Observability Requirements

- `OBS-001`: If precision/recall/f1 are dropped, log a note in `evaluator_details` explaining they are not computed for code evaluation tasks.

## Acceptance Criteria

- `AC-001`: **Given** a code trial where 3/4 test commands pass, **When** the CodeEvaluator runs, **Then** `test_pass_rate = 0.75` and at least `precision != test_pass_rate` or precision/recall/f1 are not set.
- `AC-002`: **Given** a benchmark summary table, **When** it is rendered, **Then** it does not show three identical columns for precision, recall, and F1 under the code evaluator.

## Required Tests

### Unit Tests

- `UT-001`: Verify that `precision` is not equal to `test_pass_rate` when the evaluator produces a non-trivial precision value. Covers `FR-001`.
- `UT-002`: Verify that setting `precision`/`recall`/`f1` to `0.0` (or omitting them) does not crash the `mean_std()` aggregation in `runner.py`. Covers `NFR-001`.

### Integration Tests

- `IT-001`: **Scenario**: Full benchmark run with implement-it tasks
  **Given** the benchmark runner executes implement-it tasks
  **When** the CodeEvaluator scores each trial
  **Then** precision/recall/f1 are not identical to test_pass_rate (or are absent)
  Covers `AC-001`.

### Not applicable

- `SMK-001`: Not applicable — no deploy behavior changed.
- `E2E-001`: Not applicable — no user journey changed.
- `REG-001`: Not applicable — no known previous defect.
- `PT-001`: Not applicable — no performance impact.
- `ST-001`: Not applicable — no security impact.
- `UX-001`: Not applicable — no user-facing change.
- `OT-001`: Not applicable — no operational behavior changed.

## Definition of Done

- CodeEvaluator no longer sets precision/recall/f1 to copies of test_pass_rate.
- All existing tests pass.
- `bench-run` output for implement-it tasks shows only test_pass_rate and accuracy as meaningful metrics.
