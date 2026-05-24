---
id: "039"
created: 2026-05-24
updated: 2026-05-24
status: active
---

# Task: Fix implement-it measurement gaps

## Priority

P1 — Benchmark results for implement-it are currently missing structural quality signal and misreporting output token counts; both distort skill comparison data.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; changes are confined to existing evaluator registration and adapter token-counting logic.

## Assignability

**AFK** — All changes are fully specified: add one evaluator name to five JSON files, and update one token-count expression in the pi adapter.

## Context

The benchmark run on 2026-05-24 with `pi-agent` + `openai-codex/gpt-5.4-mini` revealed two measurement gaps in the implement-it pipeline:

**Gap 1 — behave evaluator never runs.**
Every implement-it task JSON declares `"evaluators": ["code"]`. The runner invokes evaluators strictly from that list, so `BehaveEvaluator` is never called. `behave_pass_rate` is always `0.0` regardless of whether the agent wrote the required `implementation/*.md` summary files. The implement-it behave feature file (`benchmarks/features/implement-it.feature`) already exists and checks structural output (directory presence, file naming, required sections). Adding `"behave"` to the evaluator list is all that is needed to activate it.

**Gap 2 — output_tokens counts only markdown, not code.**
`PiAgentAdapter.run()` computes `output_tokens = _approx_tokens(raw_output)` where `raw_output` is built from `_OUTPUT_GLOBS` (only `*.md` files). Python implementation files are in the workspace snapshot and are evaluated by `CodeEvaluator`, but their token count is excluded from `output_tokens`. The resulting `output_tokens ≈ 130` misrepresents agent effort; actual code output is invisible to the metric.

The fix: count output tokens over all files in the workspace snapshot (excluding scaffolding scripts), consistent with how `CodeEvaluator` and `BehaveEvaluator` already use `workspace_snapshot`.

## Use Cases

- **Feature**: implement-it benchmarking
- **Scenario**: Benchmark run measures structural output quality
- **Given** an implement-it benchmark run completes for 5 tasks
- **When** results are aggregated
- **Then** `behave_pass_rate` reflects whether the agent wrote compliant `implementation/*.md` summaries

- **Scenario**: Output token metric reflects actual agent work
- **Given** the agent writes 800 tokens of Python and 130 tokens of markdown
- **When** `output_tokens` is recorded
- **Then** `output_tokens` is approximately 930, not 130

## Definition of Ready

- `benchmarks/features/implement-it.feature` exists (confirmed: it does).
- `BehaveEvaluator` is registered under `"behave"` in `evaluator_registry` (confirmed: it is).
- `workspace_snapshot` contains all agent-written files including `.py` files (confirmed: `_workspace.py` captures all non-script files).

## Functional Requirements

- `FR-001`: All five implement-it task JSON files (`001` through `005`) must declare `"evaluators": ["code", "behave"]`.
- `FR-002`: `PiAgentAdapter.run()` must compute `output_tokens` by summing `_approx_tokens(content)` over all values in `workspace_snapshot`, falling back to `_approx_tokens(raw_output)` when the snapshot is empty.

## Non-Functional Requirements

- `NFR-001`: The change to `output_tokens` must not alter any other `TaskResult` field; only the `output_tokens` and `total_tokens` values change.
- `NFR-002`: Adding `"behave"` to evaluators must not cause the runner to fail when `implement-it.feature` contains scenarios the agent cannot satisfy — failing scenarios lower `behave_pass_rate` but do not raise exceptions.

## Observability Requirements

- `OBS-001`: Not applicable — the harness has no production telemetry; benchmark metrics are logged to MLflow via the existing `Tracker`.

## Acceptance Criteria

- `AC-001`: **Given** a benchmark run for `implement-it`, **When** results are printed, **Then** `behave_pass_rate` is a non-zero value (or explicitly zero because the agent failed the scenarios, not because behave was skipped).
- `AC-002`: **Given** an agent that writes one Python file of ≥500 tokens and a markdown summary of 130 tokens, **When** `output_tokens` is computed, **Then** `output_tokens ≥ 600`.
- `AC-003`: **Given** all five implement-it task JSONs, **When** each is parsed, **Then** `"behave"` appears in the `evaluators` list of every file.

## Required Tests

### Unit Tests

- `UT-001`: Test that when `workspace_snapshot = {"impl/solution.py": "x" * 500, "implementation/001-summary.md": "y" * 50}`, `output_tokens` computed via the new formula is greater than the old formula's result (which only counted markdown). Covers `FR-002`, `AC-002`.

### Integration Tests

- `IT-001`: **Scenario**: Behave evaluator runs for implement-it task  
  **Given** a `TaskResult` with a workspace snapshot containing `implementation/001-summary.md`  
  **When** the evaluator pipeline for an implement-it task runs  
  **Then** `result.behave_pass_rate` is set by `BehaveEvaluator` (not left at its default `0.0`)  
  Covers `FR-001`, `AC-001`.

### Smoke Tests

Not applicable — no deployment or startup path.

### End-to-End Tests

Not applicable — covered by integration test above.

### Regression Tests

Not applicable — no known previous defect.

### Performance Tests

Not applicable — token counting is O(n) over file content; no latency constraint.

### Security Tests

Not applicable — no trust boundary or user input involved.

### Usability Tests

Not applicable — CLI tool, no UI.

### Observability Tests

Not applicable — `OBS-001` is not applicable.

## Definition of Done

- Code is implemented in `benchmarks/harness/adapters/pi_agent.py` and five files in `benchmarks/tasks/implement-it/`.
- `UT-001` and `IT-001` pass.
- A benchmark re-run shows `behave_pass_rate` is non-default and `output_tokens` is substantially higher than 130.
- No other `TaskResult` fields are altered.
- API contracts, user-facing behavior, ADRs, or operational runbooks are documented when changed.
