---
id: "033"
date: 2026-05-23
status: complete
---

# Implementation: Add behave_pass_rate to terminal benchmark report

## Files changed

- `benchmarks/run.py` — added `("behave_pass_rate", "Behave Pass Rate")` to `metrics_to_show` after `quality_score` and before `test_pass_rate`.

## Behavior implemented

`behave_pass_rate` now appears in the `_print_summary()` terminal table. When absent from a result (no behave features for the skill), the existing `get(key, (0.0, 0.0))` fallback renders `0.000` as required by NFR-002.

## Tests added or updated

None — UT/IT not applicable per task specification; this is a list-literal addition with no logic to unit-test.

## Validations run

- Change is a single-line list entry; no logic altered; existing tests unaffected.

## ADRs updated

None.
