# ADR Implementation Rules

## When to check ADRs

Before implementing, check for relevant ADRs when the task involves:

- architecture boundaries
- dependency direction
- database choice or schema strategy
- external providers
- queues, caches, storage, or protocols
- observability standards
- security or authorization model
- scalability decisions

Good:
- Read `docs/adrs/001-use-notification-port.md` before implementing invitation email delivery.
- Read `docs/adrs/002-store-project-events.md` before writing audit events.
- Read `docs/adrs/003-use-opentelemetry.md` before adding traces.

Bad:
- Ignore ADRs because the task looks small.
- Implement provider-specific code before checking the provider boundary.
- Change the architecture direction without updating an ADR.

## Planning ADR vs implementation ADR

Planning phase:
- ADR may be `Proposed`.
- ADR captures context, options, recommendation, and open questions.

Implementation phase:
- Validate the ADR against real code constraints.
- Update status to `Accepted`, `Rejected`, or `Superseded`.
- Record consequences discovered during implementation.
- Link the implementation issue, PR, or commit if available.

Good:
- Update ADR from `Proposed` to `Accepted` after implementation confirms the notification port works.
- Add a negative consequence when the adapter adds retry complexity.
- Supersede an ADR when the implementation proves the chosen boundary is wrong.

Bad:
- Leave an accepted architecture decision undocumented.
- Keep an ADR proposed after code depends on it.
- Change direction silently in code.
- Create an ADR after the implementation is already coupled.

## When to create a new ADR during implementation

Create a new ADR when implementation reveals a meaningful decision that was not captured during planning. Apply the same criteria used during planning to decide whether the decision warrants an ADR.

## ADR update format

When updating an ADR, keep it short and decision-focused.

Update:

- Status
- Decision
- Consequences
- Validation
- Open Questions

Good:
- Status changed to `Accepted` after integration tests pass.
- Consequences note added adapter complexity.
- Open questions list retry policy for future work.

Bad:
- Paste implementation logs into the ADR.
- Omit consequences.
- Remove open questions without resolving them.

## Task dependency rule

If a task depends on an ADR, the implementation must respect it.

Good:
- Domain service depends on `NotificationPort` because ADR requires provider isolation.
- Tests verify no provider SDK import exists in domain logic.
- Implementation summary mentions ADR updated to `Accepted`.

Bad:
- Import provider SDK in domain logic despite ADR.
- Ignore ADR because direct SDK call is faster.
- Update code but leave ADR stale.