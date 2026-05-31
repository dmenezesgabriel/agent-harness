# ADR Guidelines

Architecture Decision Records capture decisions that are hard to reverse or have wide blast radius. Write a stub in `docs/adrs/` — do not write a full prose essay.

## Write an ADR when the decision is…

**Hard to reverse**
- Choice of database engine (PostgreSQL vs MongoDB vs Cassandra)
- ORM or query builder selection
- Message broker (Kafka vs RabbitMQ vs SQS)
- Cloud provider or managed service lock-in
- API protocol (REST vs GraphQL vs gRPC)

**Cross-cutting**
- Authentication strategy (JWT, session, OAuth provider)
- Authorization model (RBAC, ABAC, policy engine)
- Error handling contract (error codes, envelope format, HTTP status mapping)
- Structured logging format and correlation ID scheme
- Distributed tracing approach

**Boundary-defining**
- Monolith vs microservices split
- Sync vs async communication between components
- Event sourcing vs CRUD state model
- Multi-tenancy strategy

## Do NOT write an ADR for

- Naming conventions within a single file
- Library version pins
- Folder organization details that can be changed without cascading impact
- Formatting or linting rule choices
- Temporary implementation shortcuts that will be revisited in the same sprint

## ADR stub format

Use the template at `../plan-it/assets/adr-template.md`. At minimum, fill in:

```
# ADR-NNN: <Decision title>

## Status
Proposed

## Context
<One paragraph: what forced this decision?>

## Decision
<One sentence: what we will do.>

## Consequences
- <Positive consequence>
- <Negative consequence or trade-off>
```

Number ADRs sequentially (`001`, `002`, …). File as `docs/adrs/<NNN>-<kebab-title>.md`.
