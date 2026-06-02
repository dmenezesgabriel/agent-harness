---
id: "2026-06-02-skill-evaluator-per-fixture-structural-checks"
issue: "inline request: mitigate aggregated multi-fixture structural check risk"
status: completed
completed: 2026-06-02
---

# Implementation: Per-fixture structural checks

## Changes

### `skills/skill-evaluator/runner/runner/adapters/behave.py`

- Detects generated or baseline artifact directories named after input fixtures, such as `input_timeseries`.
- Runs Behave structural checks once per input artifact directory instead of once over the aggregate parent directory.
- Prefixes generated scenario names with the input fixture stem, for example `input_timeseries: Skill produces at least one chart artifact`.
- Preserves aggregate behavior for single-fixture output and nested artifact directories that are not input fixture directories.

### Tests

- Added regression coverage proving each input artifact directory is checked independently.
- Added regression coverage proving non-input nested directories still use aggregate behavior.
- Added reporting coverage proving fixture-labeled generated checks compare correctly against baseline rows.

## Acceptance Criteria Verification

| Item | Status | Evidence |
|------|--------|----------|
| One fixture cannot hide another fixture failure | PASS | Behave runs separately for each `input_*` artifact directory. |
| Reports identify the failing input | PASS | Scenario names are prefixed with the fixture directory name. |
| Baseline comparison remains aligned | PASS | Skill and baseline rows share the same fixture-prefixed scenario names. |
| Single-fixture behavior remains compatible | PASS | Non-input nested artifact directories still run as one aggregate output. |

## Validation

```
uv run pytest
121 passed in 0.40s
```
