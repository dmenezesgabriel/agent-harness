---
id: "032"
issue: "tasks/issues/032-fix-opencode-token-accumulation.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Fix OpenCode adapter token count accumulation

## Related Task

- `tasks/issues/032-fix-opencode-token-accumulation.md`

## Overall Verdict

**Pass**

No Blocking findings.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | IT-001 | Integration test IT-001 is absent. Requires `opencode` CLI which is not available in the development environment. Unit tests (UT-001, UT-002) cover the same parsing logic; the DoD's explicit criteria are satisfied. | Not applicable — missing file. |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `benchmarks/harness/adapters/opencode.py:127,129` uses `+=` to accumulate. `benchmarks/tests/test_opencode.py:36` (`test_accumulates_tokens_across_steps`) verifies 3-step input (100+200+50=350) and output (20+30+10=60). |
| AC-002 | Pass | Two tests verify zero tokens with no crash: `benchmarks/tests/test_opencode.py:52` (text-only NDJSON) and `benchmarks/tests/test_opencode.py:62` (empty string). Variables initialized to 0 at `opencode.py:108`. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `benchmarks/tests/test_opencode.py:36` — 3-step NDJSON, verifies 350/60. Covers FR-001. |
| Unit (UT-002) | Present | `benchmarks/tests/test_opencode.py:52` (text-only NDJSON, verifies 0/0) and `test_opencode.py:62` (empty string, verifies 0/0). Covers NFR-002. |
| Integration (IT-001) | Missing | Requires `opencode` CLI installation. See F-001. |
| Smoke (SMK-001) | Not applicable | No deploy behavior. |
| E2E (E2E-001) | Not applicable | No user journey. |
| Regression (REG-001) | Not applicable | No previous defect. |
| Performance (PT-001) | Not applicable | No performance impact. |
| Security (ST-001) | Not applicable | No security impact. |
| Usability (UX-001) | Not applicable | No user-facing change. |
| Observability (OT-001) | Not applicable | No operational behavior changed. |

## Observability Evaluation

Not applicable — OBS-001 states no new observability is required.

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

None. The test file follows the same patterns as `benchmarks/tests/test_code_evaluator.py` (fixtures, `from __future__ import annotations`, `pytest` imports, docstring conventions, file-level comment referencing the task).

## Unresolved Assumptions or Follow-Up

- IT-001 cannot be executed without the `opencode` CLI. A follow-up task could add an integration test that mocks `subprocess.run` to exercise the full `run()` → `_parse_output()` path without a live CLI.
