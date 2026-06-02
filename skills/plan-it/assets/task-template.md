---
id: "{{NUMBER}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
status: active
---

# Task: <clear task name>

## Priority

<P0 | P1 | P2> — <short reason this task has this priority>.

Example:
- P0 — Required before member invitations because projects must exist first.

## Dependencies

- <Dependency 1>
- <Dependency 2>
- <No task dependency; can start after...>
- <No ADR dependency; this task uses existing architecture.>

Example:
- Depends on Task 1: Create project.
- Depends on ADR `docs/adrs/001-use-notification-port.md`.
- Depends on the `projects` table with `id`, `name`, `description`, and `ownerId`.
- Depends on the authentication middleware exposing `currentUser.id`.
- No task dependency; can start after the API contract is approved.
- No ADR dependency; this task uses existing architecture.

## Assignability

<**AFK** — fully specified, safe to delegate to an autonomous agent without human review mid-task.>

OR

<**HITL** — requires human involvement at a decision point: [describe the specific decision or judgment that needs a human].>

Example:
- **AFK** — all requirements and acceptance criteria are resolved; no irreversible architectural decisions remain open.
- **HITL** — requires human approval of the database migration strategy before persistence can be implemented.

## Context

<Short self-contained explanation of the task. Include enough context to understand it without previous discussion.>

Example:
- Users create projects from the dashboard before they invite members or configure settings.
- A project has a name, optional description, owner, member list, and settings page.
- Only the project owner can invite members or change project settings.

<!-- Optional: include a Mermaid diagram here if the diagram merit rule is satisfied — see references/diagram-rules.md. Include only when ≥3 components interact or the flow cannot be expressed in ≤3 bullet points. -->

## Use Cases

Use Gherkin. Highlight reserved words in bold.

- **Feature**: <feature name>
- **Scenario**: <real user or system scenario>
- **Given** <initial context>
- **When** <action happens>
- **Then** <business outcome is achieved>

Example:
- **Feature**: Project creation
- **Scenario**: Team lead starts a client project
- **Given** Ana is a signed-in team lead
- **When** Ana creates a project named “Acme Migration”
- **Then** Ana can manage work for that client inside the project

## Definition of Ready

- <Specific condition required before work starts>
- <Specific contract, model, rule, or decision that must exist>
- <Specific dependency that must be available>
- <Required ADR stub exists when the task depends on an architectural decision>

Example:
- The `POST /projects` API contract includes request, response, and error formats.
- The `project.name`, `project.description`, and `project.ownerId` fields are defined.
- The owner, admin, and member permission rules are documented.
- ADR `docs/adrs/001-use-notification-port.md` exists because this task depends on the notification boundary.

## Functional Requirements

- `FR-001`: <specific behavior the system must provide>
- `FR-002`: <specific validation, rule, or action>
- `FR-003`: <specific user-visible or system-visible behavior>

Example:
- `FR-001`: A signed-in user can create a project from the dashboard.
- `FR-002`: The system rejects project names longer than 80 characters.
- `FR-003`: A project owner can invite a member using their email address.

## Non-Functional Requirements

- `NFR-001`: <specific measurable quality constraint>
- `NFR-002`: <specific reliability, performance, accessibility, localization, or compatibility constraint>
- `NFR-003`: <specific consistency or maintainability constraint>

Example:
- `NFR-001`: Project creation returns a response in under 300 ms at p95 under normal load.
- `NFR-002`: API validation errors use the same `{ code, message, field }` format.
- `NFR-003`: All project form labels, buttons, and errors use localization keys.

## Observability Requirements

- `OBS-001`: <specific log requirement>
- `OBS-002`: <specific metric requirement>
- `OBS-003`: <specific tracing requirement>
- `OBS-004`: <specific analytics requirement>
- `OBS-005`: <specific sensitive-data exclusion rule>

Example:
- `OBS-001`: Log project creation with `projectId`, `ownerId`, request ID, and result.
- `OBS-002`: Record a `project.created` metric with success and failure counts.
- `OBS-003`: Trace `POST /projects` across API, service, repository, and database calls.
- `OBS-004`: Track `project_create_succeeded` once after successful creation.
- `OBS-005`: Do not log project descriptions, emails, tokens, passwords, or personal secrets.

## Acceptance Criteria

Use observable pass/fail outcomes. Prefer Gherkin.

- `AC-001`: **Given** <context>, **When** <action>, **Then** <observable result>.
- `AC-002`: **Given** <context>, **When** <action>, **Then** <observable result>.
- `AC-003`: **Given** <context>, **When** <action>, **Then** <observable result>.

Example:
- `AC-001`: **Given** a signed-in user, **When** they submit a valid project form, **Then** the project appears on the dashboard.
- `AC-002`: **Given** a project name with 81 characters, **When** the user submits the form, **Then** the name field shows a validation error.

## Required Tests

Choose the smallest meaningful test set for this task.
Do not create tests only to satisfy a category.
Assess every category explicitly. If a category is not relevant,
mark it as not required with a specific, task-bound reason.

### Risk Assessment

| Category | Required | Reason if not required |
|----------|----------|-----------------------|
| Unit | (Yes / No) | <specific reason> |
| Integration | (Yes / No) | <specific reason> |
| Smoke | (Yes / No) | <specific reason> |
| End-to-End | (Yes / No) | <specific reason> |
| Regression | (Yes / No) | <specific reason> |
| Performance | (Yes / No) | <specific reason> |
| Security | (Yes / No) | <specific reason> |
| Usability | (Yes / No) | <specific reason> |
| Observability | (Yes / No) | <specific reason> |

The assessment table must cover every category above. Each excluded
category must cite a task-specific reason (not a generic "n/a").

### [Category selected as Required above]

- `<ID>`: <description>. Covers `<FR/AC/Risk ID>`.

Example for Unit Tests:

### Unit Tests

- `UT-001`: Validate that `project.name` accepts 1–80 characters. Covers `FR-002`.

Example for Integration Tests:

### Integration Tests

- `IT-001`: **Scenario**: Project is persisted through the API  
  **Given** a signed-in user with ID `user-123`  
  **When** they call `POST /projects` with name "Acme Migration"  
  **Then** the database stores `name`, `description`, and `ownerId`  
  **And** the API returns `201`  
  Covers `FR-001`, `AC-001`.

Example for Security Tests:

### Security Tests

- `ST-001`: Attempt to update another user's project and verify the API returns `403`. Covers `AC-004`.

## Definition of Done

- Code is implemented behind the correct domain, service, component, or adapter boundary.
- Required tests for this task pass.
- Loading, empty, validation, server error, and permission-denied states are handled where applicable.
- Required telemetry is implemented and verified.
- Required ADRs are updated from `Proposed` to `Accepted` or left with explicit open questions.
- API contracts, user-facing behavior, ADRs, or operational runbooks are documented when changed.