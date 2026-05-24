---
id: "038"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Align CLI and champion reports to RunSummary

## Priority

P1 — User-facing. Depends on 035 and 036; can start once both are complete.

## Dependencies

- Depends on Task 035: `RunSummary` type and renamed `Tracker` methods must exist.
- Depends on Task 036: `BenchmarkRunner.run_experiment()` must have removed `n_trials`, `use_judge`, and `with_skill_only` parameters.

## Assignability

**AFK** — All CLI flag removals, output column changes, and champion metric renames are fully specified.

## Context

`run.py` and `champion.py` were written for the paired experiment model. After tasks 035–036:

- `run.py` still exposes `--trials`, `--with-skill-only`, and `--judge` flags that reference removed parameters.
- `_print_summary` shows a "With skill" vs "Without skill" comparison table that no longer maps to `RunSummary.metrics`.
- `champion.py` reads `with_skill__f1__mean`, `with_skill__behave_pass_rate__mean`, etc. from MLflow — keys that `MLflowTracker.log_summary` no longer writes (it now writes `metrics__*` keys).

This task updates all three entry points to the new model without introducing new behavior.

## Use Cases

- **Feature**: Benchmark reporting
- **Scenario**: Developer runs a benchmark and reads results
- **Given** a completed benchmark run
- **When** the CLI prints the summary table
- **Then** the table shows one metric column (not a with/without comparison) with pass rates, quality score, latency, and token counts

- **Feature**: Champion comparison
- **Scenario**: Developer compares two skill variants
- **Given** two skill variants benchmarked with `--skill-dir`
- **When** `bench-compare --skill plan-it` is run
- **Then** the table shows `metrics__behave_pass_rate__mean` and `metrics__quality_score__mean` for each variant

## Definition of Ready

- Task 035 complete: `RunSummary.metrics: dict[str, tuple[float, float]]` exists.
- Task 036 complete: `run_experiment()` no longer accepts `n_trials`, `use_judge`, or `with_skill_only`.

## Functional Requirements

- `FR-001`: `run.py` removes the `--trials` CLI option.
- `FR-002`: `run.py` removes the `--with-skill-only` CLI option.
- `FR-003`: `run.py` removes the `--judge` / `--no-judge` CLI options.
- `FR-004`: `_print_summary` replaces the four-column "With skill / Without skill / Δ / p-value / Cohen's d" table with a two-column "Metric / Value (mean±std)" table reading from `RunSummary.metrics`.
- `FR-005`: `champion.py` `bench-compare` reads `metrics__behave_pass_rate__mean`, `metrics__f1__mean`, and `metrics__quality_score__mean` MLflow metric keys (replacing the old `with_skill__*` prefix).
- `FR-006`: The `test_tracker.py` `OT-001` test (`dry_run_cli`) is updated to invoke the CLI without removed flags and assert on `RunSummary` (not `ExperimentSummary`).

## Non-Functional Requirements

- `NFR-001`: No new CLI flags are added in this task.
- `NFR-002`: The `--skill`, `--platform`, `--model`, `--task-ids`, `--skill-dir`, `--tracking-uri`, and `--dry-run` flags are retained unchanged.
- `NFR-003`: `bench-promote` is unchanged (it tags by content hash, not metric keys).

## Observability Requirements

Not applicable — no new telemetry paths introduced.

## Acceptance Criteria

- `AC-001`: **Given** the updated CLI, **When** `run.py --help` is printed, **Then** `--trials`, `--with-skill-only`, and `--judge` do not appear.
- `AC-002`: **Given** a completed run producing `RunSummary(metrics={"behave_pass_rate": (0.85, 0.0)})`, **When** `_print_summary` is called, **Then** the table shows `0.850 ± 0.000` without a "Without skill" column.
- `AC-003`: **Given** MLflow runs with `metrics__behave_pass_rate__mean` keys, **When** `bench-compare --skill plan-it` is run, **Then** the table shows the correct `behave_pass_rate` values.
- `AC-004`: **Given** the updated CLI invocation without `--trials`, **When** `run.py` is called via `CliRunner`, **Then** exit code is 0 and `run_experiment` is called without `n_trials`.

## Required Tests

### Unit Tests

Not applicable — `_print_summary` and `bench-compare` are reporting functions with no isolated logic to test independently of their output.

### Integration Tests

- `IT-001`: **Scenario**: CLI invokes run_experiment without removed parameters  
  **Given** a patched `run_experiment` and a minimal tasks directory  
  **When** `run.py` is invoked via `CliRunner` with `--skill plan-it --platform pi-agent --dry-run`  
  **Then** exit code is 0 and `run_experiment` is called without `n_trials`, `use_judge`, or `with_skill_only` arguments  
  Covers `FR-001`, `FR-002`, `FR-003`, `AC-004`.

- `IT-002`: **Scenario**: `_print_summary` renders RunSummary without comparison columns  
  **Given** a `RunSummary` with `metrics={"behave_pass_rate": (0.85, 0.0), "accuracy": (1.0, 0.0)}`  
  **When** `_print_summary` is called  
  **Then** the output contains `0.850` and does not contain "Without skill" or "p-value"  
  Covers `FR-004`, `AC-002`.

### Smoke Tests

Not applicable — no startup or deploy path changed.

### End-to-End Tests

Not applicable — no complete user journey changed.

### Regression Tests

Not applicable — no previously broken defect.

### Performance Tests

Not applicable — reporting is not performance-sensitive.

### Security Tests

Not applicable — no auth or trust boundary changed.

### Usability Tests

Not applicable — this is a developer-facing CLI tool; no accessibility or form validation concern.

### Observability Tests

Not applicable — no new telemetry introduced.

## Definition of Done

- `run.py`: `--trials`, `--with-skill-only`, `--judge` options removed; `_print_summary` renders single-metric table from `RunSummary.metrics`.
- `champion.py`: `bench-compare` reads `metrics__*` MLflow keys.
- `test_tracker.py` `OT-001`: updated CLI invocation, asserts `RunSummary`.
- All tests pass.
