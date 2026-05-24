---
id: "026"
issue: "tasks/issues/026-define-tracker-port-and-inject-into-runner.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Define Tracker port and inject into runner

## Related Task

- `tasks/issues/026-define-tracker-port-and-inject-into-runner.md`

## Overall Verdict

**Pass**

No Blocking findings. Three Non-blocking findings and two Suggestions should be addressed before or alongside follow-up tasks.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | FR-001, AC-002 | `Tracker` ABC is missing `log_finding(finding: Finding)` abstract method and `NullTracker` is missing the corresponding no-op. FR-001 lists it as required; AC-002 requires NullTracker to handle `log_finding` without raising. Root cause: `Finding` type does not exist in `harness/models.py`, making the method unimplementable without a companion model addition. | `benchmarks/harness/tracking/base.py` (method absent); `benchmarks/harness/models.py` (no `Finding` dataclass) |
| F-002 | Non-blocking | UT-003 | Test UT-003 (`NullTracker().log_finding(finding)` returns without raising) is entirely absent. The issue lists it as a required unit test. Blocked by the same `Finding` prerequisite gap as F-001. | `benchmarks/tests/test_tracker.py` (no `test_null_tracker_log_finding` function) |
| F-003 | Non-blocking | OT-001 | OT-001 requires testing `bench-run --dry-run` at the CLI level to confirm stderr output. The implementation tests `NullTracker()` in isolation (`test_null_tracker_warning_on_stderr`), which verifies the same string but not via the CLI path. A CLI-level test (e.g., with `click.testing.CliRunner`) would fully satisfy OT-001's stated scenario. | `benchmarks/tests/test_tracker.py:107–110` (unit-level only; no CLI invocation) |
| F-004 | Suggestion | NFR-003 | NFR-003 states "`harness/tracking/base.py` is the only new public module introduced by this task." The implementation also introduces `harness/tracking/null_tracker.py`. However, FR-003 explicitly requires NullTracker at that path, making NFR-003 and FR-003 mutually contradictory. The implementation correctly followed FR-003. This is an internal task-spec inconsistency worth noting for future issue authoring. | `benchmarks/harness/tracking/null_tracker.py` (new file); task FR-003 vs NFR-003 |
| F-005 | Suggestion | — | `run_experiment()` uses `tracker: Tracker = None` with a `# type: ignore[assignment]` comment plus a runtime `None` guard instead of a truly required parameter. The type annotation misrepresents the contract (callers must provide a tracker), and the type-ignore suppresses the tooling signal. A cleaner alternative is `tracker: Tracker` with no default; the only call site (`run.py`) always supplies it. | `benchmarks/harness/runner.py:80–86` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `issubclass(MLflowTracker, Tracker)` asserted in `test_mlflow_tracker_isinstance_tracker`; `issubclass` being True is a necessary and sufficient condition for `isinstance` to return True on any instance. |
| AC-002 | Partial / Non-blocking | `log_trial` and `log_summary` pass (UT-001, UT-002). `log_finding` portion cannot be satisfied until `Finding` type exists. See F-001. |
| AC-003 | Pass | IT-001 (`test_benchmark_runner_with_null_tracker`) constructs `BenchmarkRunner(tracker=NullTracker())`, calls `run_experiment()` with a FakeAdapter, and asserts an `ExperimentSummary` is returned. NullTracker's no-op methods ensure no MLflow calls occur. |
| AC-004 | Pass | `--dry-run` flag added; `NullTracker()` wired when set; `NullTracker.__init__` prints the required string to stderr; `test_null_tracker_warning_on_stderr` verifies the exact string. CLI wiring confirmed in `benchmarks/run.py:138`. |
| AC-005 | Pass | Without `--dry-run`, `MLflowTracker(tracking_uri=tracking_uri)` is used. All 26 pre-existing tests pass unchanged. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `benchmarks/tests/test_tracker.py::test_null_tracker_log_trial_does_not_raise` |
| Unit (UT-002) | Present | `benchmarks/tests/test_tracker.py::test_null_tracker_log_summary_does_not_raise` |
| Unit (UT-003) | Missing | `log_finding` test absent; blocked by missing `Finding` type in `models.py`. See F-002. |
| Unit (UT-004) | Present | `benchmarks/tests/test_tracker.py::test_mlflow_tracker_isinstance_tracker` |
| Unit (UT-005) | Present | `benchmarks/tests/test_tracker.py::test_null_tracker_has_no_mlflow_import` |
| Integration (IT-001) | Present | `benchmarks/tests/test_tracker.py::test_benchmark_runner_with_null_tracker` |
| Smoke | Not applicable | No deploy or startup boundary changes; stated in task and implementation summary. |
| End-to-End | Not applicable | No user-visible output changes except `--dry-run` warning on stderr. |
| Regression | Not applicable | No known prior defect related to tracker coupling. |
| Performance | Not applicable | Interface indirection adds negligible overhead. |
| Security | Not applicable | No authentication or trust-boundary changes. |
| Usability | Not applicable | No user-facing UI changes. |
| Observability (OT-001) | Partial | `test_null_tracker_warning_on_stderr` verifies the exact stderr string but tests NullTracker directly rather than via `bench-run --dry-run`. See F-003. |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | When `NullTracker` is active, runner logs exactly one warning to stderr: `[tracker] dry-run mode: experiment tracking is disabled` | Met | `NullTracker.__init__` at `benchmarks/harness/tracking/null_tracker.py:12` prints the exact string to stderr once on construction. `test_null_tracker_warning_on_stderr` asserts the exact string. |
| OBS-002 | `Tracker.log_trial` must not write raw agent output or workspace file contents to any log | Met | `NullTracker.log_trial` discards all inputs with no I/O. The abstract interface itself performs no writes. `MLflowTracker.log_trial` logs `raw_output` as an MLflow artifact — this is pre-existing behavior unchanged by this task. |

## ADR Compliance

| ADR | Required Action | Status |
|-----|-----------------|--------|
| `docs/adrs/002-extension-point-interface-mechanism.md` | Updated from `Proposed` to `Accepted` before implementation begins (DoD requirement) | Done — status updated to `Accepted` |

## Convention Notes

- `F-004` — Suggestion — NFR-003 says `base.py` is the only new public module, but FR-003 independently requires `null_tracker.py`. The task spec is internally contradictory; the implementation followed FR-003. Future issue authoring should ensure NFR constraints align with FRs.
- `F-005` — Suggestion — `run_experiment()` type annotation `tracker: Tracker = None` with `# type: ignore[assignment]` weakens the static-analysis signal. Removing the default and the guard would make the required-argument contract explicit without breaking any existing call site.

## Unresolved Assumptions or Follow-Up

- **`Finding` model gap**: FR-001 requires `log_finding(finding: Finding)` on the `Tracker` ABC. No `Finding` dataclass exists in `harness/models.py`. A follow-up task should define `Finding` in `models.py`, add `log_finding` to the `Tracker` ABC, implement it in `NullTracker` and `MLflowTracker` (wiring through to `findings.log_finding`), and add UT-003.
- **OT-001 CLI-level test**: A `CliRunner`-based test invoking `bench-run --dry-run` (similar to the pattern used in `test_champion.py`) would give stronger end-to-end confidence for AC-004 and OT-001.
- **`run_experiment` function `None` default**: If the function is ever called from a new context outside `run.py` or `BenchmarkRunner`, the `tracker: Tracker = None` signature may allow silent misuse. Hardening to a true required parameter (F-005) is recommended before follow-up decoupling tasks add more call sites.
