---
id: "053"
created: 2026-05-26
updated: 2026-05-26
status: active
---

# Task: Add headless test runability requirement to plan-it test selection

## Priority

P2 — Tasks that specify required tests without requiring headless runability produce task contracts that the implementing agent cannot validate automatically. An unrunnable test is indistinguishable from a passing test in the validation loop.

## Dependencies

- No task dependency; no ADR dependency.
- Requires write access to `skills/plan-it/references/test-selection.md`.

## Assignability

**AFK** — the change is a precisely scoped addition to the intro section of the test-selection reference file.

## Context

The plan-it Skill's test-selection.md guides planners to choose the smallest meaningful test set. It does not require that specified tests be headlessly runnable with a single command. When a planner specifies an integration test that implicitly requires a manually started service or environment, the task contract inherits that implicit manual step. The implementing agent cannot automate what the planner has not specified, and the result is a test that either fails silently or is skipped during validation.

The requirement to add: any test type specified in a task must be runnable headlessly with the project's existing single test command. If the test requires setup not currently automated, the task must also include a requirement to automate that setup. This is a constraint on all test types, applicable equally to unit, integration, smoke, and all other test categories.

Target file: `skills/plan-it/references/test-selection.md`

## Use Cases

- **Feature**: Headless test specification
- **Scenario**: Planner specifies an integration test requiring a running database
- **Given** the plan-it Skill includes the headlessness constraint
- **When** the planner writes the integration test requirement
- **Then** the planner also includes in the task's functional requirements: "The test database must be started automatically by the test suite setup" — so the implementer knows setup automation is required, not assumed

## Definition of Ready

- `skills/plan-it/references/test-selection.md` introduction section is readable and its current wording is known.

## Functional Requirements

- `FR-001`: The test-selection.md introduction section is extended to state that all specified tests must be runnable headlessly with the project's existing single test command.
- `FR-002`: The requirement states that if a specified test requires setup not currently automated, the planner must add a functional requirement to the task to automate that setup.
- `FR-003`: The requirement applies to all test types (unit, integration, smoke, E2E, regression, performance, security, usability, observability).

## Non-Functional Requirements

- `NFR-001`: The addition is in the introduction section so it applies to all test types, avoiding repetition across each type's subsection.
- `NFR-002`: The guidance does not reference other skills by name.

## Observability Requirements

Not applicable — this task edits a Markdown reference file with no runtime telemetry.

## Acceptance Criteria

- `AC-001`: **Given** the updated test-selection.md, **When** the introduction section is read, **Then** it includes the headlessness constraint applying to all test types.
- `AC-002`: **Given** the constraint, **When** it is read, **Then** it requires that setup automation be added as a functional requirement if the test needs it.
- `AC-003`: **Given** the updated file, **When** the entire file is read, **Then** no other skill is referenced by name.

## Required Tests

### Unit Tests

Not applicable — this task edits a Markdown reference file, not executable code.

### Integration Tests

Not applicable — no executable integration boundary exists in this change.

### Smoke Tests

- `SMK-001`: **Scenario**: Updated test-selection.md introduction contains the headlessness constraint  
  **Given** the file has been updated  
  **When** the introduction section is read  
  **Then** the headlessness constraint is present and applies to all test types  
  Covers `FR-001`.

### End-to-End Tests

Not applicable — no complete user journey changes; this is a reference file edit.

### Regression Tests

Not applicable — no known previous defect specific to this text edit.

### Performance Tests

Not applicable — text-only change with no runtime performance impact.

### Security Tests

Not applicable — no authentication, authorization, or trust boundary is touched.

### Usability Tests

Not applicable — this is a reference file, not a user interface.

### Observability Tests

Not applicable — this task does not introduce or modify operationally observable behavior.

## Definition of Done

- `skills/plan-it/references/test-selection.md` introduction includes the headlessness constraint applying to all test types with the setup-automation clause.
- No other skill is referenced by name in the updated file.
