---
id: "026"
issue: tasks/issues/026-define-tracker-port-and-inject-into-runner.md
created: 2026-05-23
updated: 2026-05-23
---

# Implementation Summary: Define Tracker port and inject into runner

## Task implemented

Issue 026 — Define Tracker port and inject it into the runner.

## Files changed

| File | Change |
|---|---|
| `benchmarks/harness/tracking/base.py` | **New** — `Tracker` ABC with `log_trial` and `log_summary` abstract methods |
| `benchmarks/harness/tracking/null_tracker.py` | **New** — `NullTracker` no-op implementation; prints warning to stderr on construction |
| `benchmarks/harness/tracking/tracker.py` | Modified — `MLflowTracker` now inherits `Tracker` |
| `benchmarks/harness/tracking/__init__.py` | Modified — exports `Tracker` and `NullTracker` |
| `benchmarks/harness/runner.py` | Modified — `run_experiment` accepts `tracker: Tracker` (required); added `BenchmarkRunner` class |
| `benchmarks/run.py` | Modified — added `--dry-run` flag; wires `NullTracker` when set, `MLflowTracker` otherwise |
| `benchmarks/tests/test_tracker.py` | **New** — unit and integration tests for the tracker port |
| `docs/adrs/002-extension-point-interface-mechanism.md` | Updated status from `Proposed` to `Accepted` |

## Behavior implemented

- `Tracker` ABC in `harness/tracking/base.py` defines `log_trial` and `log_summary` abstract methods matching the existing `MLflowTracker` signatures.
- `MLflowTracker` inherits `Tracker`; `isinstance(MLflowTracker(...), Tracker)` returns `True` without instantiation needed (verified via `issubclass`).
- `NullTracker` in `harness/tracking/null_tracker.py` implements both methods as no-ops, imports nothing from `mlflow`, and prints `[tracker] dry-run mode: experiment tracking is disabled` to stderr exactly once on construction.
- `BenchmarkRunner` class added to `runner.py` with `tracker: Tracker` constructor parameter; delegates to the module-level `run_experiment` function.
- `run_experiment` function now requires `tracker` — the internal `tracker = tracker or MLflowTracker()` fallback is removed; passing `None` raises `TypeError`.
- `bench-run --dry-run` wires `NullTracker`; without the flag, `MLflowTracker` is used as before.

## Design notes

- The existing `run_experiment` function signature retained for CLI backward compatibility; `BenchmarkRunner` wraps it to satisfy FR-005 and AC-003.
- `tracker: Tracker = None` with a `None` guard is used instead of a bare required positional arg to preserve keyword-argument compatibility at call sites.

## Tests added

| Test ID | Test name | Covers |
|---|---|---|
| UT-001 | `test_null_tracker_log_trial_does_not_raise` | FR-003, AC-002 |
| UT-002 | `test_null_tracker_log_summary_does_not_raise` | FR-003 |
| UT-004 | `test_mlflow_tracker_isinstance_tracker` | FR-002, AC-001 |
| UT-005 | `test_null_tracker_has_no_mlflow_import` | FR-004 |
| OT-001 | `test_null_tracker_warning_on_stderr` | OBS-001 |
| IT-001 | `test_benchmark_runner_with_null_tracker` | FR-005, AC-003 |

## Validations run

- `pytest tests/` — 26 passed, 0 failed (all pre-existing tests continue to pass).

## ADRs updated

- `docs/adrs/002-extension-point-interface-mechanism.md` — updated from `Proposed` to `Accepted`. Implementation confirms the ABC pattern is consistent with the existing `adapters/base.py` and `evaluators/base.py` and `isinstance` checks work as expected.

## Observability added

- `NullTracker.__init__` writes one line to stderr: `[tracker] dry-run mode: experiment tracking is disabled`.

## Skipped or not-applicable test categories

- **UT-003 (`log_finding`)** — Not implemented. The `Finding` type referenced in FR-001 and the class diagram does not exist in `harness/models.py`. The existing `log_finding` in `findings.py` is a module-level function, not a `Tracker` method. Adding it to the ABC would require a companion model change outside this task's scope.
- **Smoke tests** — Not applicable; no deploy or startup boundary changed.
- **End-to-end tests** — Not applicable; only stderr output changes with `--dry-run`.
- **Regression tests** — Not applicable; no known prior defect.
- **Performance tests** — Not applicable; interface indirection adds negligible overhead.
- **Security tests** — Not applicable; no authentication or trust-boundary changes.
- **Usability tests** — Not applicable; no UI changes.
- **Accessibility checks** — Not applicable; no UI was touched.

## Unresolved assumptions / follow-up work

- `Finding` model and `Tracker.log_finding` method are referenced in FR-001 / UT-003 but have no implementation in `models.py`. If `Finding` is added in a follow-up task, `Tracker`, `NullTracker`, and `MLflowTracker` will need corresponding `log_finding` methods.
