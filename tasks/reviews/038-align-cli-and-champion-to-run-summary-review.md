---
id: "038"
issue: "tasks/issues/038-align-cli-and-champion-to-run-summary.md"
created: 2026-05-24
updated: 2026-05-24
---

# Review: Align CLI and champion reports to RunSummary

## Related Task

- `tasks/issues/038-align-cli-and-champion-to-run-summary.md`

## Overall Verdict

**Pass**

No Blocking findings.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Suggestion | IT-001 | `test_cli_invokes_run_experiment_without_removed_parameters` does not patch `SkillLintValidator`, so the test depends on the real `skills/plan-it` directory being present and valid. If the directory is removed or corrupted, the CLI exits with code 1 and the test fails for an unrelated reason. | `benchmarks/tests/test_tracker.py:382–413` — `run.SkillLintValidator` not in the patch context |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `run.py` defines no `--trials`, `--with-skill-only`, or `--judge` option; confirmed by reading the full `@click.command()` block (`run.py:95–112`). |
| AC-002 | Pass | `_print_summary` formats each metric as `f"{mean:.3f} ± {std:.3f}"` (`run.py:89`), producing `0.850 ± 0.000` for `(0.85, 0.0)`. Only two columns exist: `Metric` and `Mean ± Std` — no "Without skill" column (`run.py:69–70`). IT-002 also verifies this at runtime. |
| AC-003 | Pass | `bench-compare` reads `"metrics__behave_pass_rate__mean"`, `"metrics__f1__mean"`, `"metrics__quality_score__mean"`, and `"metrics__latency_ms__mean"` via `_mean(group, ...)` (`champion.py:114–117`). `test_champion.py` fixture logs these same keys (`test_champion.py:27–28`). |
| AC-004 | Pass | IT-001 (`test_cli_invokes_run_experiment_without_removed_parameters`) asserts `result.exit_code == 0` and verifies `"n_trials"`, `"use_judge"`, and `"with_skill_only"` are absent from the captured kwargs (`test_tracker.py:411–413`). |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit | Not applicable | Issue states: no isolated logic separable from output for `_print_summary` or `bench-compare`. |
| Integration (IT-001) | Present | `test_cli_invokes_run_experiment_without_removed_parameters` at `test_tracker.py:382`. Asserts exit_code 0 and absence of `n_trials`, `use_judge`, `with_skill_only` in `run_experiment` kwargs. Covers FR-001, FR-002, FR-003, AC-004. |
| Integration (IT-002) | Present | `test_print_summary_renders_single_metric_table` at `test_tracker.py:420`. Asserts `"0.850"` present and `"Without skill"` / `"p-value"` absent. Covers FR-004, AC-002. |
| Smoke | Not applicable | No startup or deploy path changed. |
| E2E | Not applicable | No complete user journey changed. |
| Regression | Not applicable | No previously broken defect. |
| Performance | Not applicable | Reporting is not performance-sensitive. |
| Security | Not applicable | No auth or trust boundary changed. |
| Usability | Not applicable | Developer-facing CLI tool. |
| Observability | Not applicable | No new telemetry introduced. |

## Observability Evaluation

Not applicable — no OBS requirements defined in the task.

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

- `F-001` — Suggestion — IT-001 relies on the real `skills/plan-it` directory for `SkillLintValidator` validation. Other integration tests in the file (e.g., `test_benchmark_runner_with_null_tracker`) patch deeper into the stack and avoid real-filesystem dependencies. Adding `patch("run.SkillLintValidator")` would bring IT-001 into line with that pattern, but this is not required by the task contract.

## Unresolved Assumptions or Follow-Up

- None.
