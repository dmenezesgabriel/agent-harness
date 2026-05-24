---
id: "033"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Add behave_pass_rate to terminal benchmark report

## Priority

P2 — The metric is computed and stored in MLflow but invisible in the CLI output, reducing the value of running behave tests.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this task changes only a display list in `run.py`.

## Assignability

**AFK** — fully specified; one-line change to a display configuration list.

## Context

The `BehaveEvaluator` runs Gherkin scenario assertions against the agent's workspace snapshot and computes `behave_pass_rate`. This metric is stored in `TrialResult.behave_pass_rate` and logged to MLflow, but the `_print_summary()` function in `benchmarks/run.py` has a `metrics_to_show` list that does not include `"behave_pass_rate"`:

```python
metrics_to_show = [
    ("accuracy", "Accuracy"),
    ("precision", "Precision"),
    ...
    ("total_tokens", "Total Tokens"),
]
```

Adding `("behave_pass_rate", "Behave Pass Rate")` to this list will display the metric in the terminal output table.

## Use Cases

- **Feature**: Benchmark report completeness
- **Scenario**: Researcher runs a benchmark and reads the terminal report
- **Given** the experiment includes behave assertions
- **When** the report is printed
- **Then** the behave pass rate should be visible alongside accuracy, F1, and other metrics

## Definition of Ready

- The `_print_summary()` function and `ExperimentSummary` model are understood.

## Functional Requirements

- `FR-001`: Display `behave_pass_rate` in the `_print_summary()` terminal output table, after `quality_score` and before `test_pass_rate`, with label `"Behave Pass Rate"`.

## Non-Functional Requirements

- `NFR-001`: Does not require changes to models, evaluators, or data pipeline.
- `NFR-002`: If `behave_pass_rate` is absent from a summary (e.g., no behave features for the skill), display `0.000` as with other missing metrics.

## Observability Requirements

- `OBS-001`: Not applicable — no operational behavior changed.

## Acceptance Criteria

- `AC-001`: **Given** the benchmark runner prints results, **When** the terminal table is rendered, **Then** it includes a "Behave Pass Rate" row with the mean ± std for both conditions.

## Required Tests

### Not applicable

All test categories not applicable — this is a display change to CLI output with no code logic change:

- `UT-001`: Not applicable — no logic to unit-test; the change is a list literal addition.
- `IT-001`: Not applicable — no integration boundaries crossed.
- `SMK-001`: Not applicable — no deploy behavior changed.
- `E2E-001`: Not applicable — no user journey changed.
- `REG-001`: Not applicable — no previous defect.
- `PT-001`: Not applicable — no performance impact.
- `ST-001`: Not applicable — no security impact.
- `UX-001`: Not applicable — no user-facing interaction behavior changed.
- `OT-001`: Not applicable — no operational behavior changed.

## Definition of Done

- `behave_pass_rate` appears in the terminal results table when running `bench-run`.
- All existing tests pass.
