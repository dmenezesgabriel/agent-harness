---
id: "022"
created: 2026-05-19
updated: 2026-05-19
status: active
---

# Task: Apply safe review-it refactors (code review gate only)

## Priority

P2 — Can proceed after task 019 confirms the methodology. No benchmark gate exists for review-it; validation is code review and manual spot-check.

## Dependencies

- Depends on Task 019 completing: the refactor methodology is established and champion baselines are in place for plan-it and implement-it.
- No ADR dependency.

## Assignability

**AFK** — all target files, line ranges, and replacement content are fully specified. No automated benchmark gate exists for review-it; this task is deliberately lower-confidence than tasks 020 and 021.

## Context

Three low-risk changes to the review-it skill. All three are text-only edits with no logic changes:

- **R-1** (`SKILL.md:64–71`): The `Before marking complete` checklist has 8 items. Seven directly restate steps 3, 5, 7, 8, 11, 12, and 13 of the workflow the agent just executed. The one non-obvious item — "No source files were modified" — enforces the read-only invariant that has no equivalent workflow step.
- **R-2** (`SKILL.md:95–106`): The `Final response` bullet list is identical in substance to the `Final response after file generation` section in `references/output-rules.md`. Since `output-rules.md` is always read at step 13, the SKILL.md version is loaded twice. Replace with a single-line pointer.
- **X-4** (`SKILL.md:43`): Step 14 has no template reference, unlike the equivalent step in implement-it which links `../plan-it/assets/context-template.md` (a cross-skill relative path). Add a local reference `assets/context-template.md` and create `skills/review-it/assets/context-template.md` as a copy of `skills/plan-it/assets/context-template.md`.

**Note on missing benchmark coverage**: review-it has no task JSON files in `benchmarks/tasks/review-it/`, no `review-it.feature`, and no `review_evaluator.py`. Automated quality regression detection is not possible for this task. Validation relies on code review and a manual invocation spot-check. Adding full benchmark coverage for review-it is a separate follow-up.

## Use Cases

- **Feature**: Skill token efficiency
- **Scenario**: Reviewer manually invokes review-it after refactor
- **Given** the refactored review-it skill is active
- **When** the skill is invoked against a known issue file with a known implementation
- **Then** it produces a review report with all required sections: Findings, AC Evaluation, Test Coverage, Observability, ADR Compliance, Convention Notes, Unresolved Assumptions

## Definition of Ready

- Task 019 complete (methodology established).
- `skills/plan-it/assets/context-template.md` exists (source for copy).
- A sample issue file and implementation summary are available for the manual spot-check.

## Functional Requirements

- `FR-001`: `skills/review-it/SKILL.md` `Before marking complete` section contains exactly one checklist item: `[ ] No source files were modified — this skill is read-only.`
- `FR-002`: `skills/review-it/SKILL.md` `Final response` section is replaced with: `After writing the review report, summarize as specified in [output-rules.md — Final response](references/output-rules.md#final-response-after-file-generation).`
- `FR-003`: `skills/review-it/assets/context-template.md` exists and is byte-for-byte identical to `skills/plan-it/assets/context-template.md`.
- `FR-004`: `skills/review-it/SKILL.md:43` references `assets/context-template.md` (not `../plan-it/assets/context-template.md`).
- `FR-005`: The total line count of `skills/review-it/SKILL.md` after changes is at least 15 lines fewer than before.
- `FR-006`: Manual invocation of the refactored skill against a sample issue file produces a review report with all 8 required sections from `review-report-template.md`.

## Non-Functional Requirements

- `NFR-001`: No content other than the three targeted sections is modified in `SKILL.md`.
- `NFR-002`: `output-rules.md` is not modified — the pointer in `FR-002` references the existing section heading anchor.

## Observability Requirements

- `OBS-001`: Not applicable — no automated benchmark run for review-it.

## Acceptance Criteria

- `AC-001`: **Given** `skills/review-it/SKILL.md`, **When** the `Before marking complete` section is read, **Then** it contains exactly one item: the read-only reminder.
- `AC-002`: **Given** `skills/review-it/SKILL.md`, **When** the `Final response` section is read, **Then** it is a single line pointing to `output-rules.md`.
- `AC-003`: **Given** `diff skills/plan-it/assets/context-template.md skills/review-it/assets/context-template.md`, **When** the diff runs, **Then** output is empty.
- `AC-004`: **Given** `skills/review-it/SKILL.md:43`, **When** the line is read, **Then** it references `assets/context-template.md` with no `../plan-it/` prefix.
- `AC-005`: **Given** the refactored skill and a sample `tasks/issues/001-create-project.md` with known FRs and ACs, **When** the skill is invoked manually, **Then** the produced `tasks/reviews/001-create-project-review.md` contains non-empty Findings, AC Evaluation, Test Coverage, and Overall Verdict sections.

## Required Tests

### Unit Tests

- `UT-001`: Not applicable — changes are text edits with no new logic.

### Integration Tests

- `IT-001`: Not applicable — no automated benchmark for review-it exists. Follow-up task required to add `benchmarks/tasks/review-it/` task JSONs, `review-it.feature`, and `review_evaluator.py`.

### Smoke Tests

- `SMK-001`: Not applicable.

### End-to-End Tests

- `E2E-001`: Not applicable.

### Regression Tests

- `REG-001`: Not applicable.

### Performance Tests

- `PT-001`: Not applicable.

### Security Tests

- `ST-001`: Not applicable.

### Usability Tests

- `UX-001`: Not applicable.

### Observability Tests

- `OT-001`: Not applicable.

## Definition of Done

- All four ACs (AC-001 through AC-004) verified by diff and `cat`.
- `skills/review-it/SKILL.md` line count reduced by ≥ 15 lines (`wc -l` before and after).
- Manual spot-check (AC-005) confirmed against a sample issue file.
- Implementation summary documents the three changed sections and the absence of a benchmark gate, with recommendation to add review-it benchmark coverage as follow-up.
- Required telemetry is implemented and verified.
- Required ADRs are updated from `Proposed` to `Accepted` or left with explicit open questions.

## Unresolved Assumptions

- No benchmark coverage for review-it exists. The changes in this task are accepted under code review only. If the agent's review report quality degrades after R-1 removes checklist items that function as quality reminders, that regression will not be detected automatically. Adding review-it benchmark tasks (`benchmarks/tasks/review-it/`, `features/review-it.feature`, `harness/evaluators/review_evaluator.py`) is a separate follow-up task.
