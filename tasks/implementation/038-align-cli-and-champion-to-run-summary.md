---
id: "038"
task: "Align CLI and champion reports to RunSummary"
status: complete
date: 2026-05-24
---

# Implementation Summary

## Files Changed

- `benchmarks/run.py` — removed `--judge/--no-judge` CLI option, `judge: bool` parameter, judge print statement, and `--judge` docstring example
- `benchmarks/champion.py` — updated `_mean()` calls in `compare` from `with_skill__*__mean` keys to `metrics__*__mean` keys
- `benchmarks/tests/test_champion.py` — updated `mlflow_backend` fixture to log `metrics__*` keys and removed stale `n_trials` tag
- `benchmarks/tests/test_tracker.py` — added IT-001 and IT-002 integration tests

## Behavior Implemented

- **FR-001/FR-002/FR-003**: `--trials`, `--with-skill-only`, and `--judge` flags removed from `run.py`; confirmed absent in `--help` output (AC-001)
- **FR-004**: `_print_summary` already rendered a single-metric table from `RunSummary.metrics`; no change needed
- **FR-005**: `bench-compare` now reads `metrics__behave_pass_rate__mean`, `metrics__f1__mean`, `metrics__quality_score__mean`, `metrics__latency_ms__mean` — matching what `MLflowTracker.log_summary` writes
- **FR-006**: OT-001 `dry_run_cli` test already invoked CLI without removed flags; added IT-001 and IT-002 as specified

## Tests Added

- `IT-001` (`test_cli_invokes_run_experiment_without_removed_parameters`): asserts `run_experiment` receives no `n_trials`, `use_judge`, or `with_skill_only` kwargs (covers FR-001–003, AC-004)
- `IT-002` (`test_print_summary_renders_single_metric_table`): asserts output contains `0.850` and does not contain "Without skill" or "p-value" (covers FR-004, AC-002)

## Validations Run

- `uv run python -m pytest` — 118/118 passed
- `uv run python run.py --help` — confirmed removed flags absent (AC-001)

## Non-Applicable Test Categories

- Unit tests: `_print_summary` and `bench-compare` have no isolated logic separable from their output; IT-002 covers the output directly
- Smoke, E2E, Regression, Performance, Security, Usability, Observability: unchanged paths, no new behavior introduced

## Unresolved Assumptions

None.
