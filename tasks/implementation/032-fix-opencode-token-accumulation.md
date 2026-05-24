---
id: "032"
created: 2026-05-23
updated: 2026-05-23
status: implemented
---

# Implementation: Fix OpenCode adapter token count accumulation

## Files changed

- `benchmarks/harness/adapters/opencode.py` — Changed `=` to `+=` in `_parse_output()` `step_finish` handler to accumulate token counts across all steps.
- `benchmarks/tests/test_opencode.py` — New file with unit tests for token accumulation.

## Behavior implemented

`OpenCodeAdapter._parse_output()` now accumulates `input_tokens` and `output_tokens` across all `step_finish` events instead of overwriting with the last step's values. Fixes FR-001, FR-002, AC-001, AC-002.

## Tests added

- **UT-001** (`test_accumulates_tokens_across_steps`): 3-step NDJSON with known counts (100+200+50 input, 20+30+10 output) verifies accumulation to 350/60.
- **UT-002** (`test_no_step_finish_events_returns_zero_tokens`): Text-only NDJSON → zero tokens, no crash.
- **UT-002** (`test_empty_output_returns_zero_tokens`): Empty string → zero tokens, no crash.

## Validations run

Could not run in this environment (no pip/pytest available). Fix is trivially verified: `input_tokens` and `output_tokens` are initialized to 0 at line 108, and the `+=` operator on lines 127/129 ensures accumulation.

## ADRs updated

None — no architectural impact.

## Not applicable

- Integration test (IT-001) requires an actual `opencode` CLI installation — not run here.
- Smoke, E2E, regression, performance, security, UX, operational — all intentionally not applicable per task spec.

## Unresolved assumptions

- The `step_finish` token event format from `opencode run --format json` uses the documented `{"type":"step_finish","part":{"tokens":{"input":N,"output":M}}}` structure.
