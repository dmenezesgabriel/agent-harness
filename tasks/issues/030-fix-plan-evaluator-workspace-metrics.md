---
id: "030"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Fix PlanEvaluator to evaluate workspace content and fix broken metrics

## Priority

P0 — Plan-it benchmarks produce meaningless scores for file-outputting agents (OpenCode), because required sections are never found in `raw_output`. The fp=0 hardcode also makes precision always 1.0, hiding hallucinated content.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this task uses the existing `Evaluator` ABC and `TrialResult.workspace_snapshot`.

## Assignability

**AFK** — all requirements and acceptance criteria are resolved; no irreversible architectural decisions remain open.

## Context

The `PlanEvaluator` (`benchmarks/harness/evaluators/plan_evaluator.py`) scores a plan by checking whether required markdown sections (Context, Requirements, Acceptance Criteria, Tests) appear in `result.raw_output`. This works for agents that output plans as response text but fails for file-writing agents like OpenCode, which write plans into workspace files (ADRs, issue documents) and only emit a brief summary in the text output.

The evaluator has `result.workspace_snapshot` available — a dict of `{relative_path: content}` for every file the agent wrote — but never reads it.

Two additional bugs:
- `fp = 0` is hardcoded in `_score_completeness`, meaning precision is always `tp / (tp + 0) = 1.0` whenever at least one section is found. This makes the precision metric meaningless.
- `_has_classification` checks for lowercase `"afk"` / `"hitl"` but the skill uses uppercase `AFK` / `HITL` in document content. This causes classification detection to miss valid content.

## Use Cases

- **Feature**: Plan evaluator scoring
- **Scenario**: Researcher runs a plan-it benchmark with OpenCode
- **Given** an OpenCode agent writes its plan into workspace files (not response text)
- **When** the PlanEvaluator scores the trial
- **Then** it should find sections in the workspace files and produce correct metrics

- **Scenario**: Researcher reviews benchmark precision
- **Given** a plan output that includes extra sections not in the gold standard
- **When** the PlanEvaluator computes precision
- **Then** the false-positive count should be non-zero and precision should drop accordingly

## Definition of Ready

- The `TrialResult.workspace_snapshot` field is populated for all adapters and contains agent-written files.
- The required sections list and scoring rubric in `plan_evaluator.py` are understood.

## Functional Requirements

- `FR-001`: `PlanEvaluator.evaluate()` must merge content from both `result.raw_output` AND all files in `result.workspace_snapshot` before scanning for required sections.
- `FR-002`: When computing precision, `fp` must reflect the count of non-required sections present in the evaluated content (raw output + workspace files), not hardcoded 0.
- `FR-003`: The `_has_classification()` check must match both uppercase and lowercase `AFK`/`HITL` keywords.
- `FR-004`: The `_has_classification()` check must also scan workspace snapshot content, not just `raw_output`.

## Non-Functional Requirements

- `NFR-001`: Existing plan-it benchmark tasks must be scorable with unchanged gold standards.
- `NFR-002`: The evaluator must handle empty or absent `workspace_snapshot` gracefully (agents that don't write files).

## Observability Requirements

- `OBS-001`: Log whether content was sourced from `raw_output`, `workspace_snapshot`, or both in `evaluator_details`.
- `OBS-002`: Log per-task counts of sections found and false-positive sections.

## Acceptance Criteria

- `AC-001`: **Given** a trial with sections in workspace files but not in `raw_output`, **When** `PlanEvaluator.evaluate()` runs, **Then** the required sections are found and `accuracy > 0.0`.
- `AC-002`: **Given** a trial with extra sections not in the gold standard, **When** `PlanEvaluator.evaluate()` runs, **Then** `precision < 1.0` and `fp > 0`.
- `AC-003`: **Given** a trial where `workspace_snapshot` is empty, **When** `PlanEvaluator.evaluate()` runs, **Then** it falls back to `raw_output` only and does not crash.
- `AC-004`: **Given** a plan containing `## HITL Decision Point`, **When** `_has_classification()` runs, **Then** it returns `True`.

## Required Tests

### Unit Tests

- `UT-001`: Merge `raw_output` + `workspace_snapshot` and verify sections are found from both sources. Covers `FR-001`.
- `UT-002`: Compute precision with known false positives and verify `fp > 0`. Covers `FR-002`.
- `UT-003`: Assert `_has_classification()` returns `True` for content containing uppercase `AFK` and `HITL`. Covers `FR-003`.

### Integration Tests

- `IT-001`: **Scenario**: End-to-end plan evaluator with simulated file-writing agent
  **Given** a `TrialResult` with workspace files containing required sections and empty `raw_output`
  **When** `PlanEvaluator.evaluate()` runs
  **Then** the result has `accuracy >= 0.5` and `evaluator_details.sections_found > 0`
  Covers `AC-001`, `FR-001`.

### Not applicable

- `SMK-001`: Not applicable — this task changes only a scoring function, not deploy availability.
- `E2E-001`: Not applicable — no user journey changed; this is a benchmark scoring fix.
- `REG-001`: Not applicable — no known previous defect.
- `PT-001`: Not applicable — this task does not affect runtime performance.
- `ST-001`: Not applicable — this task does not touch authentication, authorization, or data handling.
- `UX-001`: Not applicable — this task has no user-facing behavior change.
- `OT-002`: Not applicable — this task does not modify operationally relevant behavior beyond logging.

## Definition of Done

- PlanEvaluator scans both `raw_output` and `workspace_snapshot` before scoring.
- Precision computation reflects actual false positives.
- Classification keywords match uppercase/lowercase variations.
- All existing tests in `benchmarks/tests/` pass.
- The `bench-run` CLI produces non-zero accuracy for plan-it tasks on OpenCode with the deepseek model.
