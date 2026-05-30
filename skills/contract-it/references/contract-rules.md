# Contract Rules

Use these rules to define interface contracts that are narrow, typed, and unambiguous before implementation begins.

## Boundary classification

Classify each contract before writing it:

| Type | What it defines | Example |
|---|---|---|
| `port` | Interface a component depends on but does not own the implementation for | `UserRepository`, `EmailPort` |
| `api` | HTTP, GraphQL, or gRPC endpoint shapes — request, response, and error | `POST /invitations` request/response/error |
| `event` | Domain event or async message schema | `UserCreatedEvent`, `InvitationSentEvent` |
| `domain-type` | Shared value object, entity, or aggregate boundary used across multiple components | `UserId`, `Email`, `Money` |

A single boundary may need more than one contract type (e.g., an API endpoint that also publishes a domain event).

## Naming conventions

### Ports
- Interface: `<Entity>Repository`, `<Service>Port`, `<Event>Publisher`, `<Resource>Reader`, `<Resource>Writer`
- Adapter (implementation): `<Tech><Entity>Repository` (e.g., `PgUserRepository`), `<Tech><Service>Client` (e.g., `SendgridEmailClient`)

### API contracts
- Request type: `<Action><Entity>Request` or `<Action><Entity>Input`
- Response type: `<Action><Entity>Response` or `<Action><Entity>Output`
- Error type: `<Entity>Error` or `<Entity>ValidationError`

### Event contracts
- Event name: `<Entity><PastTenseVerb>Event` (e.g., `UserCreatedEvent`, `InvitationExpiredEvent`)
- Event names use past tense — events describe something that already happened.

### Domain types
- Value object: noun naming the concept (`Email`, `UserId`, `Money`)
- Aggregate: entity name with no suffix (`User`, `Project`, `Invitation`)

## Narrowness rule

One interface per external capability. Never group unrelated operations into one interface.

Good:
- `UserRepository` with `findById`, `findByEmail`, `save`, `delete`
- `NotificationPort` with `send(notification: Notification): void`

Bad:
- `UserService` with `findById`, `sendInvitation`, `exportToCsv`, `generateReport`

A god-interface is one where you could remove a method without breaking all consumers. If that is true, split it.

## When to write a contract vs. skip

Write a contract when:
- Two or more components implement or consume the same interface
- A component crosses a process or service boundary (HTTP, queue, database)
- A test double is needed for the boundary in unit tests
- Parallel development requires two teams to agree on a shared type before coding

Skip a contract when:
- Only one implementation exists and no test double is needed — write the concrete class directly
- The interface is private to a single module and will not be called from outside
- A contract already exists for this boundary in the codebase — inspect before writing

## Output location rules

| Scenario | Output location |
|---|---|
| Intra-codebase port, typed language, source structure exists | Source stub in the detected ports directory (`src/application/ports/`, `internal/ports/`, etc.) |
| Cross-service API contract | `docs/contracts/<slug>.md` with the schema in OpenAPI, JSON Schema, or gRPC proto |
| Cross-service event schema | `docs/contracts/<slug>.md` with typed event definition and example payload |
| Domain type shared across bounded contexts | Source stub in the shared domain package |
| Source structure not yet established | `docs/contracts/<slug>.md` in the project's language, marked as a stub |

Prefer source stubs over docs when the source structure exists and the language is typed — source stubs are type-checked, IDE-navigable, and directly usable by implementers.

## Contract completeness rules

A contract is complete when:
- All method and field names use the project's domain vocabulary
- Every parameter and return type is explicitly named — no `any`, `object`, `dict`, or untyped functions
- Every error condition is represented as a typed return or exception type, not a comment
- All known consumers (callers and implementers) are identified

## Invariant rules

State at least one invariant per contract. An invariant is a constraint every implementation must satisfy.

Good:
- `findById` returns `null` (or `None` / `Option`) when no record exists — never throws.
- `save` is idempotent for the same entity ID.
- Event `occurredAt` is always in UTC ISO-8601.

Bad:
- "Should work correctly."
- "Handle errors appropriately."

## Clarification protocol

Ask one question at a time. Each question must include numbered alternatives, one marked `(recommended)`, concrete and mutually exclusive.

Walk decisions in this order: boundary type → consumers and implementers → operations → parameter/return types → error conditions → invariants.

Inspect the codebase before asking — existing port files, type definitions, and test doubles often answer the question.
