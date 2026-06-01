# Design Rules

Use these rules to keep implementation maintainable, testable, accessible, and easy to change.

## Design goal

Implement the task with the least design needed to be correct, testable, readable, accessible, and easy to change.

Use SOLID, design patterns, Ports and Adapters, Clean Architecture, Component-Driven Development, semantic HTML, accessibility, and Atomic Design as decision tools, not mandatory ceremonies.

Apply a principle only when it reduces current risk, clarifies responsibility, protects a volatile boundary, improves testability, improves accessibility, or follows existing project architecture.

Good:
- Add a port when provider replacement or test isolation is a real concern.
- Extract a component when multiple UI states or reuse justify it.
- Follow the existing feature-folder structure instead of forcing Atomic Design.
- Keep direct simple code when there is no volatility, duplication, or boundary risk.

Bad:
- Add an interface for every class.
- Add a repository around simple existing queries without a boundary need.
- Introduce a pattern to look "enterprise-ready."

## SOLID principles

Apply SOLID as design pressure, not ceremony.

Good:
- Keep validation rules in a validator or domain service, not scattered across UI and API.
- Depend on a notification interface instead of a provider SDK.
- Add a new strategy only when behavior genuinely varies.

Bad:
- Add interfaces for every class.
- Create factories before there are variants.
- Put business rules inside UI components.

## Ports and Adapters

Use Ports and Adapters when external systems or volatile infrastructure are involved.

Good:
- Domain service depends on `NotificationPort`.
- Email provider SDK lives in `SendGridNotificationAdapter`.
- Tests use an in-memory notification adapter.

Bad:
- Domain logic imports the email provider SDK directly.
- Provider-specific errors leak into domain rules.
- Add a port for a stable local helper with no external dependency.

## Clean Architecture boundaries

Keep dependency direction pointing inward.

Good:
- UI calls application use cases.
- Application services coordinate domain rules and ports.
- Domain logic has no framework, database, UI, or provider dependency.

Bad:
- Domain imports React, Express, Django, Prisma, or provider SDKs.
- API handler contains core domain rules.
- Infrastructure types leak into domain APIs.

## Component-Driven Development

Use CDD for frontend implementation when the task changes UI behavior.

Good:
- Define `ProjectForm` states: empty, invalid, submitting, success, server error, and permission denied.
- Verify component behavior with fixtures before wiring the real API.
- Keep component API small: inputs, outputs, events, accessible names, and labels.

Bad:
- Build the whole page before designing component states.
- Mix fetching, permission rules, formatting, validation, and rendering in one component.
- Create generic UI primitives before one real component needs them.

## Semantic HTML and accessibility

Use semantic HTML before ARIA.
Use native controls before custom controls.
Use ARIA only when native semantics are not enough.

Good:
- Use `<button>` for actions, `<a href="...">` for navigation, `<label>` for form controls.
- Use `<fieldset>` and `<legend>` for grouped form controls.
- Use headings in a logical order.
- Use landmarks (`main`, `nav`, `header`, `footer`) when they match the layout.
- Use `aria-describedby` to connect errors and help text to inputs.

Bad:
- Use `<div onClick>` as a button.
- Add `role="button"` to a `div` when `<button>` works.
- Hide focus outlines without an accessible replacement.

## Keyboard and focus behavior

Interactive UI must work with keyboard and predictable focus.

Good:
- Tab order follows the visual and logical flow.
- Dialogs move focus inside when opened and restore focus when closed.
- Error submission moves focus to the first invalid field when that is the project convention.
- Disabled controls expose clear state and do not trap focus.

Bad:
- A mouse-only menu.
- A modal that leaves focus behind the overlay.
- A hidden focus outline.

## Forms and validation accessibility

Forms must be understandable and recoverable.

Good:
- Every input has an accessible name.
- Errors appear next to the related field and are connected to it.
- Server errors are shown in a visible and announced location.
- Submission state prevents duplicates without trapping the user.

Bad:
- Error summary with no field-level errors.
- Validation only through color.
- Duplicate submit allowed during pending request.

## Atomic Design

Use Atomic Design as a vocabulary for UI composition when it helps.
Do not force it onto projects that already use another coherent structure.

Good:
- Atom: button, input, label, icon. Molecule: validated field, search box. Organism: project form, invitation panel.
- Reuse a validated field molecule across create and edit forms.
- Name components by domain meaning when domain meaning is clearer than Atomic Design labels.

Bad:
- Create atom/molecule/organism folders for a tiny one-off UI.
- Put business rules in atoms.
- Rename the project's existing component structure without a task requirement.

## Cohesion and responsibility

Each module should have one clear reason to change.

Good:
- `ProjectNameValidator` changes when name rules change.
- `CreateProjectService` changes when project creation behavior changes.
- `ProjectForm` changes when form presentation or interaction changes.

Bad:
- `projectUtils` contains validation, API calls, formatting, rendering, and permissions.
- One component handles routing, fetching, validation, authorization, analytics, and rendering.

## Coupling

Prefer stable contracts over volatile details.

Good:
- Use application-level commands like `CreateProjectCommand`.
- Keep API response shape stable with `{ code, message, field }`.
- Pass component data through explicit props instead of hidden globals.

Bad:
- Pass raw HTTP request objects through domain logic.
- Leak database row shape into UI components.
- Let UI components import persistence clients.

## Design patterns

Use design patterns only when they reduce current complexity.

Good:
- Use Strategy when multiple invitation expiration policies are real.
- Use Adapter for email, payment, storage, analytics, or external APIs.
- Use Repository when persistence details should not leak into application logic.

Bad:
- Add Strategy for one hardcoded behavior.
- Add Factory for a single constructor call.
- Add global state management for one local form.

## Naming

Use names that reveal intent and domain meaning.

Good:
- `CreateProjectService`, `ProjectInvitation`, `ownerId`, `rejectDuplicateInvitation`
- `canUpdateProjectSettings`, `ProjectForm`, `InvitationStatusBadge`

Bad:
- `Manager`, `Handler2`, `processData`, `doStuff`, `flag`, `Utils`

## Refactoring

Refactor only when it supports the task or removes local friction.

Good:
- Extract duplicate validation after adding the second real use.
- Rename a misleading method before adding behavior to it.
- Move provider code behind an adapter before adding the second provider-specific call.

Bad:
- Refactor the whole module before fixing a small bug.
- Change architecture style mid-task without an ADR.
- Rename unrelated files.

## Avoid overengineering

Do the simplest thing that satisfies current requirements and preserves likely change points.

Good:
- Add a small port for email delivery because the provider is volatile.
- Keep project creation synchronous until a real async requirement exists.
- Add one validation function instead of a validation framework.

Bad:
- Build a workflow engine for one form.
- Add plugin architecture for one integration.
- Introduce event sourcing for simple CRUD without an ADR.

## OOP Object Calisthenics

For Value Objects, entity validation, first-class collections, method indentation, and no-else rules, see [oop-calisthenics.md](oop-calisthenics.md).

## Avoid workarounds

Fix the root cause when practical.

Good:
- Fix the permission check in the service.
- Normalize API validation errors at the boundary.
- Add a regression test for the bug.

Bad:
- Hide the settings button but leave the API unprotected.
- Ignore type errors with unsafe casts or dynamic escape hatches.
- Disable a failing test without replacing coverage.
