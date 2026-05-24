---
id: "032"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Fix OpenCode adapter token count accumulation

## Priority

P1 — Token counts in benchmark results are unreliable because only the last step's values are captured, not the cumulative totals. This affects token-related metrics and cost estimation.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this task fixes a parsing bug within an existing adapter.

## Assignability

**AFK** — fully specified; all requirements and acceptance criteria are resolved.

## Context

The `OpenCodeAdapter._parse_output()` (`benchmarks/harness/adapters/opencode.py`) parses NDJSON events from `opencode run --format json`. Each `step_finish` event contains a token breakdown:

```json
{"type":"step_finish","part":{"tokens":{"total":12858,"input":12753,"output":88,"reasoning":17}}}
```

The current code:

```python
elif etype == "step_finish":
    tokens = event.get("part", {}).get("tokens", {})
    if "input" in tokens:
        input_tokens = tokens["input"]
    if "output" in tokens:
        output_tokens = tokens["output"]
```

This overwrites `input_tokens` and `output_tokens` on every `step_finish`, so the final values reflect only the LAST step's token counts, not the cumulative totals for the entire run.

For multi-step agent runs (which is the common case), this significantly underestimates total token usage and distorts cost estimation.

## Use Cases

- **Feature**: Benchmark token metering
- **Scenario**: Researcher examines token usage for an OpenCode agent trial
- **Given** an agent completes a task in 3 steps
- **When** the OpenCode adapter parses the output
- **Then** the input and output token counts should reflect the total across all steps, not just the last

## Definition of Ready

- The NDJSON event format from `opencode run --format json` is understood, including the `step_finish` token event structure.

## Functional Requirements

- `FR-001`: Parse ALL `step_finish` events and accumulate `input` and `output` token counts across all steps.
- `FR-002`: Store the accumulated totals in `TrialResult.input_tokens` and `TrialResult.output_tokens`.

## Non-Functional Requirements

- `NFR-001`: The fix must not increase latency or change the trial result for non-token metrics.
- `NFR-002`: Must handle the case where `step_finish` events are absent (e.g., empty output, error).

## Observability Requirements

- `OBS-001`: No new observability required — this task fixes existing token metrics.

## Acceptance Criteria

- `AC-001`: **Given** an OpenCode agent run with 3 steps each consuming tokens, **When** the adapter parses the output, **Then** `input_tokens == sum(input across all steps)` and `output_tokens == sum(output across all steps)`.
- `AC-002`: **Given** an OpenCode agent run with no `step_finish` events, **When** the adapter parses the output, **Then** `input_tokens == 0` and `output_tokens == 0` (no crash).

## Required Tests

### Unit Tests

- `UT-001`: Simulate multi-step NDJSON input with known per-step token counts and verify accumulation produces correct totals. Covers `FR-001`.
- `UT-002`: Simulate empty NDJSON input and verify zero tokens, no crash. Covers `NFR-002`.

### Integration Tests

- `IT-001`: **Scenario**: OpenCode adapter with multi-step task
  **Given** the OpenCode adapter runs a multi-step task via `opencode run`
  **When** the output is parsed
  **Then** the reported token counts are greater than any single step's count
  Covers `AC-001`.

### Not applicable

- `SMK-001`: Not applicable — no deploy behavior.
- `E2E-001`: Not applicable — no user journey.
- `REG-001`: Not applicable — no previous defect.
- `PT-001`: Not applicable — no performance impact.
- `ST-001`: Not applicable — no security impact.
- `UX-001`: Not applicable — no user-facing change.
- `OT-001`: Not applicable — no operational behavior changed.

## Definition of Done

- OpenCode adapter accumulates token counts across all `step_finish` events.
- Unit tests verify accumulation correctness.
- Existing test suite passes.
