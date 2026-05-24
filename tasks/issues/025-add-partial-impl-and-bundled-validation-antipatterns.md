---
id: "025"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Add partial-implementation and bundled change-and-validation anti-patterns to SKILL.md

## Priority

P1 — Depends on Task 024; the new planning-rules.md sections are only effective when also surfaced in the skill entrypoint, which agents read on every invocation before consulting any reference files.

## Dependencies

- Depends on Task 024: `planning-rules.md` must contain "Narrow scope rule" and "System integrity rule" sections so the new anti-patterns have a reference to point to.
- No ADR dependency.

## Assignability

**AFK** — single-file addition to a known section; all replacement content is specified and no architectural decisions are open.

## Context

Task 024 adds scope and integrity rules to `references/planning-rules.md`. However, agents read `SKILL.md` first on every invocation and only consult `planning-rules.md` for specific guidance. Without surfacing the new rules as anti-patterns in `SKILL.md`, agents may still produce oversized tasks before encountering the reference.

The existing "Anti-patterns to avoid" section in `skills/plan-it/SKILL.md` is read at invocation time. Two anti-patterns added there will intercept the problematic behavior immediately:

- **Partial implementations**: a task whose implementation leaves the system broken or incomplete until a subsequent task is applied.
- **Bundled change and validation**: a task that applies code or text changes and also runs benchmarks, promotes a champion, or performs other validation steps.

After the source edit, `scripts/install-skills.sh` must be run to propagate changes to `.agents/skills/plan-it/SKILL.md`.

## Use Cases

- **Feature**: Anti-pattern surfacing at invocation time
- **Scenario**: Agent reads the skill entrypoint before creating any tasks
- **Given** an agent loaded `skills/plan-it/SKILL.md`
- **When** it reads the "Anti-patterns to avoid" section
- **Then** it sees "Partial implementations" and "Bundled change and validation" listed before it generates any task

## Definition of Ready

- Task 024 is complete: `planning-rules.md` contains "Narrow scope rule" and "System integrity rule".
- `skills/plan-it/SKILL.md` is readable at that path.
- `scripts/install-skills.sh` is executable.

## Functional Requirements

- `FR-001`: The "Anti-patterns to avoid" section of `skills/plan-it/SKILL.md` must include a "Partial implementations" entry stating: do not create a task that removes or disables existing behavior without replacing it in the same task; the system must be fully functional after each task is applied independently.
- `FR-002`: The "Anti-patterns to avoid" section of `skills/plan-it/SKILL.md` must include a "Bundled change and validation" entry stating: do not put code or text changes and their benchmark or promotion steps in the same task; apply the change in one task and measure or promote in a subsequent task.
- `FR-003`: Both entries must use the bold-heading + prose format already used by the other anti-patterns in the section (e.g., **Artificial task splitting**, **Cross-section duplication**).
- `FR-004`: `scripts/install-skills.sh` is run after the source edit; `.agents/skills/plan-it/SKILL.md` matches the source.

## Non-Functional Requirements

- `NFR-001`: The two new entries must not duplicate or contradict any existing anti-pattern in the section.
- `NFR-002`: No other section of `skills/plan-it/SKILL.md` may be modified.

## Observability Requirements

- Not applicable — no runtime components are involved; all changes are to Markdown files.

## Acceptance Criteria

- `AC-001`: **Given** `skills/plan-it/SKILL.md` is read, **When** searching for "Partial implementations", **Then** the entry is found inside the "Anti-patterns to avoid" section.
- `AC-002`: **Given** `skills/plan-it/SKILL.md` is read, **When** searching for "Bundled change and validation", **Then** the entry is found inside the "Anti-patterns to avoid" section.
- `AC-003`: **Given** `scripts/install-skills.sh` was run after the edit, **When** running `diff skills/plan-it/SKILL.md .agents/skills/plan-it/SKILL.md`, **Then** no diff output.

## Required Tests

### Unit Tests

- Not applicable — changes are pure Markdown text; no executable logic exists.

### Integration Tests

- Not applicable — no system boundaries crossed.

### Smoke Tests

- `SMK-001`: **Scenario**: Partial implementations anti-pattern is present
  **Given** the source edit is complete
  **When** running `grep -n "Partial implementations" skills/plan-it/SKILL.md`
  **Then** at least one matching line is found.

- `SMK-002`: **Scenario**: Bundled change and validation anti-pattern is present
  **Given** the source edit is complete
  **When** running `grep -n "Bundled change and validation" skills/plan-it/SKILL.md`
  **Then** at least one matching line is found.

- `SMK-003`: **Scenario**: Installed file matches source
  **Given** `scripts/install-skills.sh` was run
  **When** running `diff skills/plan-it/SKILL.md .agents/skills/plan-it/SKILL.md`
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

- `skills/plan-it/SKILL.md` contains both new anti-pattern entries as specified in FR-001 and FR-002.
- Both entries use the bold-heading + prose format.
- SMK-001, SMK-002, and SMK-003 pass.
- `scripts/install-skills.sh` has been run; `.agents/skills/plan-it/SKILL.md` matches the source.
- No other section of `SKILL.md` was modified.
