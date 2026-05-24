---
id: "037"
issue: "tasks/issues/037-add-skill-lint-validator.md"
created: 2026-05-24
updated: 2026-05-24
---

# Review: Add SkillLintValidator for zero-token structural pre-check

## Related Task

- `tasks/issues/037-add-skill-lint-validator.md`

## Overall Verdict

**Pass**

No Blocking findings. Two Suggestions are noted below.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Suggestion | FR-007 | Lint validator is called after adapter construction. FR-007 only requires the check precede `run_experiment`, but placing it after `_make_adapter()` means a skill misconfiguration is discovered only if adapter construction succeeds first. Moving the check before `_make_adapter()` would fail faster and at a cheaper point. | `benchmarks/run.py:124–130` |
| F-002 | Suggestion | IT-001 | IT-001 asserts `"missing.md" in result.output`, but `run.py` prints lint errors via Rich's `console = Console()` initialized at module level. CliRunner patches `sys.stdout` after the module is imported (inside the test body), so the Console may write to the original stdout rather than CliRunner's capture buffer. If so, the output assertion would be vacuously fragile. Consider using `click.echo` for lint error output, or constructing the Console inside `main()`. | `benchmarks/run.py:42`, `benchmarks/tests/test_skill_lint.py:133–154` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `test_validate_clean_skill_dir_passes` asserts `result.passed == True` and `result.errors == []` for a skill dir with all referenced files present. |
| AC-002 | Pass | `test_validate_missing_skill_md_returns_one_error` asserts `not result.passed`, `len(result.errors) == 1`, and `"SKILL.md" in result.errors[0].message`. |
| AC-003 | Pass | `test_validate_broken_references_link` asserts one error with `"references/missing-file.md" in result.errors[0].path`. |
| AC-004 | Pass | `test_validate_two_broken_links_returns_two_errors` asserts `len(result.errors) == 2` for two broken links. |
| AC-005 | Pass | IT-001 (`test_run_exits_on_lint_failure`) invokes CLI via `CliRunner`, asserts `exit_code == 1`, `"missing.md" in result.output`, and `mock_experiment.assert_not_called()`. See F-002 for a reliability note on output capture. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001–UT-006) | Present | `benchmarks/tests/test_skill_lint.py` — all six unit tests present and linked to correct requirement IDs. |
| Integration (IT-001) | Present | `benchmarks/tests/test_skill_lint.py:133–154` — CLI runner test present. See F-002 for output assertion concern. |
| Smoke | Not applicable | No deploy or startup path changed. |
| E2E | Not applicable | No complete user journey changed. |
| Regression | Not applicable | No previously broken defect. |
| Performance | Not applicable | Validator reads only local files; no performance constraint. |
| Security | Not applicable | No auth or trust boundary involved. |
| Usability | Not applicable | Output is a developer-facing CLI error message; no UX component changed. |
| Observability | Not applicable | No telemetry introduced. |

## Observability Evaluation

Not applicable — no OBS requirements defined in the task.

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

- F-001 — Suggestion — The pattern in `run.py` is: tasks-dir check → adapter construction → lint check → experiment. Other pre-flight checks in the codebase (adapter registry lookup) also precede the lint check. Ordering the lint validator immediately after argument parsing and before any adapter instantiation is not required by the task contract but would be consistent with the spirit of "zero-token pre-flight."

## Unresolved Assumptions or Follow-Up

- The implementation summary claims "116 passed, 0 failed." This review could not independently run the test suite, so F-002's output-capture concern was not confirmed or refuted. A follow-up run of `pytest tests/test_skill_lint.py -v` would settle it.
- IT-001 invokes `main` with `--skill plan-it`, relying on `benchmarks/tasks/plan-it/` being present. This directory exists in the repo (`001-rate-limiter.json` et al.), so the precondition holds. If the task corpus is ever pruned, IT-001 would break on the tasks-dir check before reaching the lint check.
