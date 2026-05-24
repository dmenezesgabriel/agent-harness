---
id: "024"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Add narrow-scope and system-integrity rules to planning-rules.md

## Priority

P0 — Root cause of oversized issues; without explicit scope guidance agents produce tasks that bundle multiple concerns, consume excess tokens to implement, and leave the system partially broken between tasks.

## Dependencies

- No task dependency; `skills/plan-it/references/planning-rules.md` is readable and editable now.
- No ADR dependency; this is a documentation-only edit with no architectural decisions.

## Assignability

**AFK** — single-file addition; requirements and acceptance criteria are fully specified with no open decisions.

## Context

The plan-it skill currently lacks explicit rules about task scope and system integrity. Without them, agents produce issues that:

- Bundle multiple unrelated concerns (e.g., editing three different skill directories for independent reasons).
- Bundle a code change with its benchmark validation and champion promotion into one task.
- Leave the system in a degraded state that only resolves when a follow-up task is applied.

Two new sections added to `skills/plan-it/references/planning-rules.md` address this directly:

- **Narrow scope rule**: one cohesive concern per task; change tasks and validation tasks are always separate.
- **System integrity rule**: after each task is implemented in isolation the system must be fully functional — no pending follow-up task is required for basic operation.

After the source edit, `scripts/install-skills.sh` must be run to propagate changes to `.agents/skills/plan-it/references/planning-rules.md`.

## Use Cases

- **Feature**: Narrow scope enforcement
- **Scenario**: Agent plans a skill improvement that includes a text edit and a benchmark run
- **Given** an agent is planning using plan-it with the updated `planning-rules.md`
- **When** it considers bundling "apply text edits to SKILL.md" and "run benchmark and promote champion" into one task
- **Then** it creates two tasks: one for the edit, one for the validation

- **Feature**: System integrity preservation
- **Scenario**: Agent plans a two-step feature
- **Given** task 1 adds new behavior and task 2 validates it
- **When** only task 1 is implemented and deployed
- **Then** the system remains fully functional with no broken paths or incomplete stubs

## Definition of Ready

- `skills/plan-it/references/planning-rules.md` is readable at that path.
- `scripts/install-skills.sh` is executable.

## Functional Requirements

- `FR-001`: `planning-rules.md` must contain a new "Narrow scope rule" section that states:
  - One cohesive concern per task. A concern is cohesive when its changes can be described in one sentence and affect one module or component boundary.
  - Change tasks and validation tasks are always separate. Applying an edit and running a benchmark to validate it are different tasks.
  - If a task would touch unrelated modules for different reasons, split by concern.
  - Good/Bad examples illustrating each sub-rule using scenarios from the skill domain (skill edits, benchmark runs).
- `FR-002`: `planning-rules.md` must contain a new "System integrity rule" section that states:
  - After implementing a task in isolation, the system must remain fully functional.
  - No task may be a partial implementation that requires a subsequent task to restore basic operation.
  - Good example: a task adds a new rule to a reference file that is independently readable and takes effect immediately.
  - Bad example: a task removes an existing behavior with the expectation that a follow-up task will replace it.
- `FR-003`: Both new sections must follow the existing bold-heading + prose + Good/Bad example format used throughout `planning-rules.md`.
- `FR-004`: `scripts/install-skills.sh` is run after the source edit; `.agents/skills/plan-it/references/planning-rules.md` matches the source.

## Non-Functional Requirements

- `NFR-001`: The new sections must not duplicate or contradict any existing rule in `planning-rules.md`.
- `NFR-002`: Each new section heading must be reachable as a lowercase hyphenated markdown anchor.

## Observability Requirements

- Not applicable — no runtime components are involved; all changes are to Markdown files.

## Acceptance Criteria

- `AC-001`: **Given** `skills/plan-it/references/planning-rules.md` is read, **When** searching for "Narrow scope rule", **Then** the section is present and contains a Good example that separates an edit task from a benchmark task.
- `AC-002`: **Given** `skills/plan-it/references/planning-rules.md` is read, **When** searching for "System integrity rule", **Then** the section is present and contains a Bad example of a partial implementation.
- `AC-003`: **Given** `scripts/install-skills.sh` was run after the edit, **When** running `diff skills/plan-it/references/planning-rules.md .agents/skills/plan-it/references/planning-rules.md`, **Then** no diff output.

## Required Tests

### Unit Tests

- Not applicable — changes are pure Markdown text; no executable logic exists.

### Integration Tests

- Not applicable — no system boundaries crossed.

### Smoke Tests

- `SMK-001`: **Scenario**: Narrow scope rule section is present after edit
  **Given** the source edit is complete
  **When** running `grep -n "Narrow scope rule" skills/plan-it/references/planning-rules.md`
  **Then** at least one matching line is found.

- `SMK-002`: **Scenario**: System integrity rule section is present after edit
  **Given** the source edit is complete
  **When** running `grep -n "System integrity rule" skills/plan-it/references/planning-rules.md`
  **Then** at least one matching line is found.

- `SMK-003`: **Scenario**: Installed file matches source
  **Given** `scripts/install-skills.sh` was run
  **When** running `diff skills/plan-it/references/planning-rules.md .agents/skills/plan-it/references/planning-rules.md`
  **Then** no diff output.

### End-to-End Tests

- Not applicable — no user-facing application.

### Regression Tests

- Not applicable — no prior defect being guarded.

### Performance Tests

- Not applicable — no runtime behavior.

### Security Tests

- Not applicable — no trust boundaries involved.

### Usability Tests

- Not applicable — no interactive UI.

### Observability Tests

- Not applicable — no logs, metrics, or traces involved.

## Definition of Done

- `skills/plan-it/references/planning-rules.md` contains both new sections as specified in FR-001 and FR-002.
- Both sections follow the bold-heading + prose + Good/Bad format.
- SMK-001, SMK-002, and SMK-003 pass.
- `scripts/install-skills.sh` has been run; `.agents/skills/plan-it/references/planning-rules.md` matches the source.
- No other files in the skill were modified.
