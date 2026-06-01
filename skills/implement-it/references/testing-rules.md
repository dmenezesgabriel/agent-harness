# Testing Rules

Choose tests based on task risk and confidence needed. Do not add tests only to satisfy a category. Prefer the smallest test that proves the behavior.

## Test selection

Add broader tests only when the task:

- crosses real boundaries
- changes critical user flows
- modifies permissions or trust boundaries
- affects performance risk
- changes observability
- fixes a known regression
- changes behavior shared by multiple features
- changes interactive UI, forms, navigation, dialogs, or error states

If a category is not relevant, write:

```text
Not applicable — <specific reason>
```

## Test doubles

Use the lightest double that gives the test the confidence it needs.

**Dummy** — satisfies a required parameter; test doesn't use it. **Stub** — returns a fixed response; use when verifying how the subject handles a dependency's output, not whether it was called. **Spy** — stub that records calls; use when verifying a side effect occurred (email sent, event emitted, metric recorded). **Mock** — pre-programmed with exact call expectations; use only when interaction order/count is itself the behavior under test. **Fake** — lightweight working implementation (e.g., `InMemoryTestDatabase`); use in integration tests when risk is behavior, not real infrastructure.

Good:
- Stub the payment gateway to return a fixed declined response — the test verifies the service surfaces the correct error, not how many times the gateway was called.
- Spy on the email service to assert exactly one invitation email was sent — the side effect is the behavior under test.
- Fake the repository with an in-memory store when testing the service layer and the task risk is business logic, not database behavior.

Bad:
- Mock every collaborator in a unit test — the test becomes a specification of call order, not behavior.
- Replace all integration test boundaries with Mocks — that gives none of the boundary confidence.

## Unit tests

Use unit tests for isolated rules, validators, mappers, permissions, reducers, hooks, components, and domain logic.

Good:
- Validate that `project.name` accepts 1–80 characters.
- Validate that duplicate invitations are rejected for the same project and email.
- Validate that only owners can update project settings.

Bad:
- Test project creation end-to-end in a unit test.
- Snapshot the entire page for one validation rule.

## Component tests

Use component tests for frontend behavior when the project has component-test support.

Good:
- Render `ProjectForm` with an empty name and verify the name error appears.
- Render `ProjectForm` in submitting state and verify the submit button is disabled.
- Verify validation errors are associated with the related input.
- Verify the submit action is reachable by keyboard.

Bad:
- Snapshot large rendered trees without behavioral assertions.
- Skip keyboard and focus behavior for interactive components.

## Integration tests

Use integration tests for real boundaries.

Good:
- Create a project through `POST /projects` and verify the database stores `name`, `description`, and `ownerId`.
- Call `PATCH /projects/:id/settings` as a member and verify the API returns `403`.
- Submit the connected project form against a test API adapter and verify success and error states.

Bad:
- Test database mocks only.
- Call a mocked service and call it integration.

## Smoke tests

Use smoke tests for shallow post-build or post-deploy confidence.

Good:
- Verify the dashboard loads for a signed-in user.
- Verify the health endpoint returns ready after deployment.
- Verify the CLI command starts and prints help.

Bad:
- Use smoke tests to verify every validation branch.
- Replace integration tests with smoke tests.

## End-to-end tests

Use E2E tests for critical complete user journeys.

Good:
- User creates a project from the dashboard and sees it in the project list.
- Member opens project settings and sees access denied.
- User recovers from a failed save and successfully submits again.

Bad:
- Add E2E for every field validation.
- Use E2E when a unit, component, or integration test gives the same confidence.

## Regression tests

Use regression tests for known previous defects.

Good:
- Duplicate invitation still shows "Member already invited."
- Settings API still returns `403` for members after a permission refactor.
- Form submission no longer sends duplicate requests after double-click.

Bad:
- Add regression tests without linking a bug, incident, or known failure.
- Keep a regression test that no longer represents a real risk.

## Performance tests

Use performance tests for measurable latency, throughput, memory, rendering, or concurrency risk.

Good:
- Verify `POST /projects` stays under 300 ms p95 under normal load.
- Verify search typing stays under 100 ms interaction latency with 1,000 projects.

Bad:
- Add performance tests for static copy changes.
- Measure locally and treat it as production evidence.

## Security tests

Use security tests for authentication, authorization, input handling, data exposure, secrets, injection, abuse, and trust boundaries.

Good:
- Attempt to update another user's project and verify `403`.
- Save `<script>alert(1)</script>` as a project name and verify it renders as text.
- Verify logs do not contain tokens or passwords.
- Verify frontend-only permission hiding is backed by server-side authorization.

Bad:
- Only hide unauthorized UI controls.
- Skip security tests for role changes.

## Usability and accessibility tests

Use usability and accessibility tests for user-facing clarity, semantic HTML, accessible names, roles, keyboard access, focus behavior, and error recovery.

Good:
- Empty project form shows errors next to related fields.
- Keyboard user can submit the form and read validation errors.
- Required inputs have accessible names.

Bad:
- Ignore loading and error states.
- Ignore keyboard and screen-reader behavior for interactive UI.
- Verify only colors for validation state.

## Observability tests

Use observability tests for logs, metrics, traces, analytics events, and sensitive-data exclusion.

Good:
- Create a project and verify the log contains `projectId`, `ownerId`, request ID, and success result.
- Complete project creation and verify success analytics event emits once.
- Verify logs exclude descriptions, email bodies, tokens, passwords, and secrets.

Bad:
- Add logs without testing them.
- Track analytics twice on retry.

## Test quality

Tests must verify behavior, not implementation noise.

Good:
- Assert the API returns `403` for a member changing settings.
- Assert duplicate invitation returns the documented error code.
- Assert validation error is visible and associated with the correct field.

Bad:
- Assert the private helper was called.
- Snapshot the whole page for a small validation rule.
- Assert CSS class names unless styling behavior is the actual requirement.
