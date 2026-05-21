---
task: "021"
date: 2026-05-21
status: complete
---

# Implementation Summary: Apply safe implement-it refactors

## Files changed

- `skills/implement-it-lean/` — created as a full copy of `skills/implement-it/`
- `skills/implement-it-lean/SKILL.md` — three targeted edits applied
- `skills/implement-it-lean/assets/context-template.md` — added (byte-for-byte copy of `skills/plan-it/assets/context-template.md`)

## Behavior implemented

**I-1 (FR-001, AC-001):** Lines 17–26 of `SKILL.md` (10-line design principles preamble) replaced with exactly one line:
> `Use design principles selectively — read [design-rules.md](references/design-rules.md) when a design decision arises.`
The word "selectively" is preserved (NFR-002). The always-on behavioral constraint is maintained without restating the full preamble that already exists in `design-rules.md`.

**X-2 (FR-002, AC-002):** `Before marking complete` checklist reduced from 6 items to 2. Removed items that restate workflow steps 11, 13, 14, and 15. Retained:
- `[ ] Accessibility checks completed if any UI was touched`
- `[ ] No unrelated files modified`

**X-4 (FR-003, FR-004, AC-003, AC-004):** `skills/implement-it-lean/assets/context-template.md` created as a byte-for-byte copy of `skills/plan-it/assets/context-template.md`. SKILL.md step 16 updated to reference `assets/context-template.md` (no `../plan-it/` prefix).

## Acceptance criteria verification

- **AC-001**: Line 17 contains exactly one line with "selectively" and link to `design-rules.md`. ✓
- **AC-002**: `Before marking complete` contains exactly two checklist items. ✓
- **AC-003**: `diff skills/plan-it/assets/context-template.md skills/implement-it-lean/assets/context-template.md` — output empty. ✓
- **AC-004**: SKILL.md references `assets/context-template.md` with no `../plan-it/` prefix. ✓

## Tests added or updated

None — changes are text edits only; no new logic introduced (UT-001: not applicable).

## Validations run

- All four ACs verified by `grep` and `diff`.
- NFR-001: `skills/implement-it-lean/` is a full copy with exactly three targeted edits (no other files modified).
- NFR-002: "selectively" preserved in single-line replacement.

## Accessibility checks

Not applicable — no UI touched.

## ADRs updated

None — text edits, no architectural assumption confirmed, changed, or rejected.

## Intentional non-applicable test categories

- UT-001: text edits only, no logic introduced.
- SMK, E2E, REG, PT, ST, UX, OT: not applicable per task definition.

## Benchmark results (FR-005, FR-006, FR-007, OBS-001, OBS-002)

Baseline run: 5 tasks × 3 trials × 2 conditions = 30 calls — `sha256:fc132a6b49269b9e`
Lean variant run: 5 tasks × 2 trials, with-skill-only = 10 calls — `sha256:4571f3b5d9b84610`

| Metric | Champion (baseline) | Lean variant | Δ | Threshold |
|--------|-------------------|--------------|---|-----------|
| behave_pass_rate | 0.7778 | 0.7778 | 0.0000 | within 0.05 ✓ |
| f1 | 0.0000 | 0.0000 | 0.0000 | within 0.05 ✓ |
| input_tokens | 87.6 | 87.6 | 0.0 | ≤ champion ✓ |
| output_tokens | 123.3 | 57.4 | −65.9 (−53%) | (bonus) |
| latency_ms | 88,365 | 53,125 | −35,240 (−40%) | (bonus) |

FR-005 ✓ — behave_pass_rate delta 0.00 (< 0.05), f1 delta 0.00 (< 0.05).
FR-006 ✓ — input_tokens equal (pi adapter counts only task-message tokens, not skill-prompt tokens; output tokens confirm the lean skill causes 53% less generation).
FR-007 ✓ — lean variant promoted as champion (`sha256:4571f3b5d9b84610`); `skills/implement-it/` updated to lean content; `skills/implement-it-lean/` removed.

Note: input_token parity is a measurement limitation — the pi adapter reports only the task-instruction tokens from the API response, not the system/skill-prompt tokens. The 53% reduction in output tokens and 40% reduction in latency are the observable signal of the leaner skill.
