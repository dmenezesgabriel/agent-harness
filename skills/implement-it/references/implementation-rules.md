# Implementation Rules

Use these rules to implement tasks safely, directly, and without unnecessary complexity.

## Implementation scope

Implement only what the assigned issue, task, story, or user request requires.

Do not add unrelated features.
Do not rewrite working code unless needed for the task.
Do not hide failures with workarounds.
Do not fragment code into many tiny modules without a clear design reason.
Do not introduce a new architectural style when the project already has a clear working structure.

Good:
- Implement project creation through the existing service boundary.
- Add validation for project names where input rules already live.
- Update only the affected form, API handler, service, repository, and tests.

Bad:
- Rewrite the whole dashboard to fix one route.
- Add a generic framework for future project workflows.
- Introduce Atomic Design folders into a project that already has a consistent feature-based structure.

## Module depth heuristic

Before adding a new abstraction, apply the deletion test:

Imagine deleting the proposed module entirely. If its complexity vanishes — callers handle it trivially — it is a pass-through. Do not add it. If its complexity reappears across multiple callers, the module is earning its keep.

A deep module has a small interface that hides a large implementation. A shallow module exposes nearly as much complexity in its interface as it has inside — it adds a layer without reducing cognitive load.

Good:
- `NotificationPort` hides SMTP, SES, and retry logic behind `send(notification)`. Deleting it scatters provider details into every call site. Deep module — justified.
- `ProjectValidator` consolidates five name rules used by API and UI. Deleting it duplicates them in two places. Deep module — justified.

Bad:
- `ProjectServiceFactory` constructs one service with no variation. Deleting it pushes a single constructor call to the caller. Shallow module — not justified.

## Codebase exploration

Inspect the codebase before asking questions when the answer can be discovered.

Look for:
- existing issue file or task description
- related tests
- existing domain models, services, use cases, or handlers
- existing components and UI states
- existing adapters, repositories, and routes
- existing validation, telemetry, and accessibility patterns
- existing ADRs

Good:
- Search for an existing project creation flow before adding a new one.
- Read current permission checks before implementing a new role rule.
- Inspect existing telemetry helpers before adding logs or metrics.
- Inspect existing component stories or examples before creating a new component API.

Bad:
- Ask where validation belongs before checking the codebase.
- Create a new folder structure without reading current architecture.
- Add custom ARIA widgets before checking whether native controls are already used.

## Clarification rule

Ask only when the task cannot be implemented safely from the issue, codebase, tests, docs, or ADRs.

Ask one question at a time. Include numbered alternatives; mark the recommended one with `(recommended)`.

Good:
- Question: Should duplicate project names be rejected per owner?
  1. Reject duplicates per owner. `(recommended)`
  2. Allow duplicates with different IDs.
  3. Reject duplicates globally.

Bad:
- What should I do?
- Any other requirements?
- Is this correct?

## TDD workflow

Use Test-Driven Development for logic, services, APIs, domain rules, permissions, data transformations, regressions, and backend behavior.

Default loop:

1. Add the smallest meaningful failing test.
2. Implement the simplest correct behavior.
3. Refactor while tests stay green.
4. Repeat until the task is complete.

Good:
- Add a unit test for the 80-character project name limit before implementing validation.
- Add an integration test for `POST /projects` persistence before wiring the repository.
- Add a regression test before fixing a known duplicate-invitation bug.

Bad:
- Write tests only after manual implementation.
- Add snapshot tests that only freeze markup.
- Skip tests because the change looks small but is risky.

## Component-Driven Development workflow

Use Component-Driven Development for frontend UI work.

Build and verify the smallest useful component or composition before wiring the full page.

Default loop:

1. Identify the component boundary.
2. Define props, inputs, events, states, and accessibility behavior.
3. Implement semantic HTML and native controls first.
4. Verify loading, empty, error, disabled, success, focus, keyboard, and permission states.
5. Compose the component into the page or flow.
6. Add integration or E2E coverage only when the composed behavior needs it.

Good:
- Build `ProjectForm` with valid, invalid, submitting, and server-error states before wiring the dashboard.
- Verify keyboard navigation and error announcements before composing the full settings page.
- Use existing story, preview, fixture, or component test patterns when available.

Bad:
- Build the whole page before testing component behavior.
- Add E2E tests for every visual state instead of component-level behavior tests.
- Use clickable `div` elements for buttons or links.

## Semantic HTML and accessibility

Accessibility is part of implementation, not final polish. See [design-rules.md — Semantic HTML and accessibility](design-rules.md#semantic-html-and-accessibility), [Keyboard and focus behavior](design-rules.md#keyboard-and-focus-behavior), and [Forms and validation accessibility](design-rules.md#forms-and-validation-accessibility).

## Vertical-slice implementation

Prefer a thin, working vertical slice over isolated horizontal layers.

Good:
- Implement form, API route, service rule, repository, success message, and telemetry for project creation together.
- Implement invitation request, permission check, record, pending state, and audit log together.

Bad:
- Build every database table before any user flow works.
- Build all UI screens before connecting real behavior.
- Add every repository method before one user flow works.

## Validation loop

Run the smallest relevant validation set after each meaningful change.

Use available project commands first.

Common validation command names:

```bash
npm test
npm run test
npm run lint
npm run typecheck
npm run build
pnpm test
pnpm lint
pnpm typecheck
pnpm build
yarn test
yarn lint
yarn typecheck
yarn build
pytest
ruff check .
mypy .
go test ./...
cargo test
dotnet test
mvn test
gradle test
```

Good:
- Run the specific unit test after changing a validator.
- Run the API integration test after changing the service and repository.
- Run typecheck after changing shared interfaces.
- Run accessibility checks when interactive UI, forms, dialogs, or error states changed.

Bad:
- Skip validation because the change looks simple.
- Run only lint after changing business logic.
- Skip accessibility checks after changing a form.

## Error handling

Handle expected failures explicitly: return structured errors (`{ code, message, field }`) with the correct HTTP status; show inline field-level errors; preserve focus or announce failures on form submission; log with safe context only (never tokens, passwords, or raw payloads). Never catch-and-ignore, return generic `500` for validation failures, or use UI hiding as a fix.

## Observability during implementation

Implement telemetry when required by the task, risk, or existing pattern.

Good:
- Log project creation with `projectId`, `ownerId`, request ID, and result.
- Emit `project.created` metric with success and failure tags.
- Trace API, service, repository, and database spans for critical flows.
- Exclude descriptions, email bodies, tokens, passwords, and secrets from logs.

Bad:
- Add logs, metrics, or analytics without specificity — no raw payloads, no unnamed metrics, no duplicate events.

## Completion rule

Implementation is complete only when:

- task behavior is implemented
- required tests pass
- relevant validations pass
- architecture boundaries are respected
- frontend semantic HTML, accessibility, and state behavior are handled when applicable
- observability requirements are satisfied when applicable
- ADRs are updated when applicable
- implementation summary is written
