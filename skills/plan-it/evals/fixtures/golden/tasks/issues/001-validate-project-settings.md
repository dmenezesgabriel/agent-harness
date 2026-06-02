---
id: "001"
created: 2026-06-01
updated: 2026-06-01
status: active
---

# Task: Validate project settings form

## Priority

P0 — Required before project settings can reject invalid input consistently.

## Dependencies

- No task dependency; can start after the existing settings form route is available.
- No ADR dependency; this task uses existing form validation architecture.

## Assignability

**AFK** — requirements and acceptance criteria are resolved; no architecture decision remains open.

## Context

Project owners update project name and description from the settings form. The form already saves valid settings, but it needs field-level validation before submit.

## Use Cases

- **Feature**: Project settings validation
- **Scenario**: Owner fixes an invalid project name
- **Given** Ana is editing project settings
- **When** Ana submits an empty project name
- **Then** the name field shows a required-field error

## Definition of Ready

- The existing settings form route is available.
- The project name and description fields are already rendered.
- The existing save action remains the persistence path for valid submissions.

## Functional Requirements

- `FR-001`: The project name field rejects empty values.
- `FR-002`: The project name field rejects values longer than 80 characters.
- `FR-003`: The description field rejects values longer than 500 characters.

## Non-Functional Requirements

- `NFR-001`: Validation errors appear without changing the existing successful save flow.

## Observability Requirements

- `OBS-001`: Do not log project names or descriptions when validation fails.

## Acceptance Criteria

- `AC-001`: **Given** an empty project name, **When** Ana submits the form, **Then** the name field shows a required error.
- `AC-002`: **Given** an 81-character project name, **When** Ana submits the form, **Then** the name field shows a length error.
- `AC-003`: **Given** valid settings, **When** Ana submits the form, **Then** the existing save behavior still succeeds.

## Required Tests

### Risk Assessment

| Category | Required | Reason |
|----------|----------|--------|
| Unit Tests | Yes | Isolation risk for name/description length rules |
| Integration Tests | Yes | Existing save behavior must be preserved through the real action |
| Smoke Tests | No | No deploy availability change — form validation only |
| End-to-End Tests | No | Covered by focused unit and integration tests, no new critical journey |
| Regression Tests | No | No known previous defect for this validation behavior |
| Performance Tests | No | O(n) on short strings — no measurable latency risk |
| Security Tests | No | No auth, authorization, or data-exposure boundary touched |
| Usability Tests | Yes | Error placement and inline feedback affects UX |
| Observability Tests | Yes | Sensitive-data logging rule must be verified |

### Unit Tests

- `UT-001`: Validate project name and description length rules. Covers `FR-001`, `FR-002`, and `FR-003`.

### Integration Tests

- `IT-001`: **Scenario**: Valid settings still save through the existing action  
  **Given** a project owner submits valid settings  
  **When** the save action runs  
  **Then** the project settings are persisted.  
  Covers `AC-003`.

### Usability Tests

- `UX-001`: Verify validation errors appear beside the relevant field. Covers `AC-001` and `AC-002`.

### Observability Tests

- `OT-001`: Verify failed validation does not log project names or descriptions. Covers `OBS-001`.

## Definition of Done

- Validation rules are implemented for name and description.
- Tests listed above pass with the project test command.
- Existing successful save behavior still works for valid settings.
