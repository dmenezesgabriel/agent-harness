---
id: "029"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Extract statistical analysis from the runner into a dedicated module

## Priority

P1 — eliminates a crosscutting concern from the runner; makes the statistical math independently testable; can be developed in parallel with Tasks 027 and 028.

## Dependencies

- No task dependency — this is a pure extraction of existing runner logic into a new module; it does not depend on the DI pattern from Task 026.
- No ADR dependency — extracting a computation into its own module is not an architecture-shaping decision.
- `harness/runner.py` must be read to identify all statistical computation code (Wilcoxon signed-rank test, Cohen's d).
- `harness/models.py` must be read to confirm where `p_value`, `effect_size`, and related fields are stored in `ExperimentSummary`.

## Assignability

**AFK** — all requirements and acceptance criteria are fully resolved; no open decisions remain.

## Context

`runner.py` mixes experiment orchestration with statistical computation: Wilcoxon signed-rank test and Cohen's d effect size are computed inline alongside trial loop logic. This couples the statistical contract to the runner's internal structure, makes the math impossible to unit-test without running a full experiment, and prevents reuse in `corpus_qc.py` or future analysis scripts. This task moves all statistical computation to `harness/analysis.py`, defines a `TrialStats` dataclass for results, and has the runner call `analyze_trials()` and store the result in `ExperimentSummary`.

## Use Cases

- **Feature**: Independently testable statistical analysis
- **Scenario**: Developer validates statistical correctness in isolation
  - **Given** two Python lists of float scores (`with_scores`, `without_scores`)
  - **When** `analyze_trials(with_scores, without_scores)` is called from a unit test
  - **Then** a `TrialStats` dataclass is returned with `p_value`, `effect_size`, `significant`, and `note`
  - **And** no adapter, runner, or tracker import is needed

- **Scenario**: Runner delegates analysis computation
  - **Given** a completed experiment with N trial pairs
  - **When** the runner finishes collecting all `TrialResult` objects
  - **Then** it calls `analyze_trials()` once per metric and stores each `TrialStats` in `ExperimentSummary`

## Definition of Ready

- `harness/runner.py` has been read to identify the exact Wilcoxon and Cohen's d code to migrate.
- `harness/models.py` has been read to confirm `ExperimentSummary` field names where statistics are stored.
- No other module imports statistical functions directly from `runner.py` (verify with grep).

## Functional Requirements

- `FR-001`: `harness/analysis.py` defines `analyze_trials(with_scores: list[float], without_scores: list[float]) -> TrialStats`.
- `FR-002`: `TrialStats` is a `dataclass` with fields: `p_value: float`, `effect_size: float`, `test_name: str`, `significant: bool` (True when `p_value < 0.05`), and `note: str` (human-readable summary of the result).
- `FR-003`: `analyze_trials()` runs a Wilcoxon signed-rank test when `len(with_scores) >= 5`; sets `significant=False` and populates `note` with an explanation when fewer than 5 paired samples are available.
- `FR-004`: `analyze_trials()` computes Cohen's d as `(mean_with - mean_without) / pooled_std`; sets `effect_size=0.0` and explains zero variance in `note` when `pooled_std == 0`.
- `FR-005`: `analyze_trials()` raises `ValueError` with a descriptive message when either input list is empty.
- `FR-006`: `runner.py` calls `analyze_trials()` for each numeric metric and stores the returned `TrialStats` in `ExperimentSummary`; all direct `scipy.stats` imports are removed from `runner.py`.
- `FR-007`: `harness/analysis.py` imports only `statistics`, `math`, `scipy.stats`, and `dataclasses` — no imports from `harness/runner.py`, `harness/adapters/`, `harness/evaluators/`, or `harness/tracking/`.

## Non-Functional Requirements

- `NFR-001`: `harness/analysis.py` has no transitive dependency on MLflow, subprocess, or any adapter or evaluator module.
- `NFR-002`: `analyze_trials()` is deterministic — identical inputs produce identical outputs.

## Observability Requirements

- `OBS-001`: Not applicable — statistical analysis is a pure computation; no logging, metrics, or traces are needed.

## Acceptance Criteria

- `AC-001`: **Given** `with_scores=[0.9, 0.95, 0.85, 1.0, 0.8, 0.88]` and `without_scores=[0.3, 0.4, 0.35, 0.25, 0.3, 0.32]`, **When** `analyze_trials()` is called, **Then** `TrialStats.p_value < 0.05` and `TrialStats.effect_size > 0` and `TrialStats.significant is True`.
- `AC-002`: **Given** `with_scores=[0.8, 0.6]` and `without_scores=[0.5, 0.4]` (fewer than 5 pairs), **When** `analyze_trials()` is called, **Then** `TrialStats.significant is False` and `TrialStats.note` is non-empty.
- `AC-003`: **Given** `with_scores=[0.5, 0.5, 0.5, 0.5, 0.5]` and `without_scores=[0.5, 0.5, 0.5, 0.5, 0.5]` (zero variance), **When** `analyze_trials()` is called, **Then** `TrialStats.effect_size == 0.0` and `TrialStats.note` is non-empty.
- `AC-004`: **Given** `analyze_trials([], [0.5])`, **When** called, **Then** `ValueError` is raised.
- `AC-005`: **Given** `runner.py` after this task, **When** grepped for `scipy`, **Then** no `scipy` import is found in `runner.py`.
- `AC-006`: **Given** `harness/analysis.py`, **When** all its imports are inspected, **Then** none reference `harness.runner`, `harness.adapters`, `harness.evaluators`, or `harness.tracking`.

## Required Tests

### Unit Tests

- `UT-001`: `analyze_trials()` with a clear signal (5+ pairs with meaningful gap) returns `p_value < 0.05` and `significant=True`. Covers `FR-003`, `AC-001`.
- `UT-002`: `analyze_trials()` with fewer than 5 pairs returns `significant=False` and a non-empty `note`. Covers `FR-003`, `AC-002`.
- `UT-003`: `analyze_trials()` with identical scores (zero variance) returns `effect_size=0.0` and a non-empty `note`. Covers `FR-004`, `AC-003`.
- `UT-004`: `analyze_trials([], [0.5])` raises `ValueError`. Covers `FR-005`, `AC-004`.
- `UT-005`: `analyze_trials([0.5], [])` raises `ValueError`. Covers `FR-005`.
- `UT-006`: `analyze_trials()` with the same inputs called twice returns identical `TrialStats`. Covers `NFR-002`.

### Integration Tests

- `IT-001`: **Scenario**: Runner summary contains `TrialStats` after extraction
  - **Given** `BenchmarkRunner(tracker=NullTracker())` with a fake adapter that returns deterministic trial scores and a fake evaluator
  - **When** `run_experiment()` completes
  - **Then** the returned `ExperimentSummary` contains a `TrialStats` field with non-None `p_value` and `effect_size`
  Covers `FR-006`.

### Smoke Tests

Not applicable — no startup or deploy boundary.

### End-to-End Tests

Not applicable — no user-visible output change; `ExperimentSummary` values are identical to before.

### Regression Tests

Not applicable — no known previous defect related to statistical computation.

### Performance Tests

Not applicable — statistical computation at experiment scale (≤50 trial pairs) is fast; no performance risk.

### Security Tests

Not applicable — no trust boundary, input-handling, or data-exposure changes.

### Usability Tests

Not applicable — no user-facing behavior change.

### Observability Tests

Not applicable — no log, metric, or trace changes.

## Definition of Done

- `harness/analysis.py` exists with `analyze_trials()` and `TrialStats`.
- `runner.py` has no direct `scipy` imports.
- `ExperimentSummary` in `harness/models.py` includes `TrialStats` per metric (or a dict of `TrialStats`).
- `UT-001` through `UT-006` and `IT-001` pass.
- All existing tests pass without modification.
