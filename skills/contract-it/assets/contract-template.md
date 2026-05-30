---
id: "{{SLUG}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
boundary: "{{port | api | event | domain-type}}"
language: "{{typescript | python | go | rust | java | kotlin | openapi | pseudo}}"
status: draft
---

# Contract: <boundary name>

## Boundary Type

<port | api | event | domain-type>

## Purpose

<1–2 sentences: what this boundary separates and why it needs a contract.>

Example:
- Separates the invitation use case from email delivery. The use case calls this interface; adapters implement it. Allows swapping providers and injecting a test double in unit tests.

## Contract Definition

<Actual typed code or schema in the project's language. See references/type-patterns.md for idiomatic patterns per language.>

Example (TypeScript port):
```typescript
export interface InvitationEmailPort {
  send(invitation: PendingInvitation): Promise<void>;
}
```

Example (Python Protocol):
```python
class InvitationEmailPort(Protocol):
    def send(self, invitation: PendingInvitation) -> None: ...
```

Example (Go interface):
```go
type InvitationEmailPort interface {
    Send(ctx context.Context, invitation PendingInvitation) error
}
```

## Consumers

| Component | Relationship |
|---|---|
| <component name> | calls / implements / subscribes / publishes |

Example:
| `SendInvitationUseCase` | calls — depends on `InvitationEmailPort` |
| `SendgridEmailAdapter` | implements — production email delivery |
| `FakeEmailAdapter` | implements — test double for unit tests |

## Invariants

- <Constraint every implementation must satisfy. Describe observable behavior, not intent.>

Example:
- `send` does not throw on delivery failure — it returns or raises a typed error result.
- `send` is idempotent for the same invitation ID within a 24-hour window.
- Implementations must not log invitation content — only `invitationId` and `recipientId`.

## Open Questions

- <Unresolved design decision about this contract.>
- None.

Example:
- Should failed delivery retry synchronously here or be delegated to a queue?
- Should the port accept a raw email address or a fully constructed `PendingInvitation`?
