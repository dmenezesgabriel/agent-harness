# Backend TDD Route

## When to use

Use this route when the change is mainly in backend or domain behavior:

- business rules
- invariants or validation
- state transitions
- service or use-case behavior
- persistence behavior owned by backend policy
- API behavior whose main complexity is behind the transport layer

## First protection

Start with one failing behavior test for the rule that is changing.

Prefer the smallest example that proves the behavior. If changing risky existing logic, add characterization coverage first where needed.

Protect observable behavior, invariants, and public contracts rather than private helpers or call order unless no stable external boundary exists.

## Owning boundary

Put the rule where it is owned:

- domain object for invariants and state rules
- use case or service for workflow policy
- adapter or contract boundary for translation concerns

Do not spread the same rule across controller, handler, repository, and caller code.

## Smallest safe loop

1. Write one failing test for the required behavior.
2. Implement the smallest passing change at the owning boundary.
3. Refactor only while tests stay green.
4. Add the next case only when a new example forces it.

Keep policy independent from framework and infrastructure where practical.

## Design checks

- protect invariants at the owner
- keep dependency direction toward stable policy
- separate decision logic from I/O and other side effects where practical
- add seams only when they improve safety or testability
- avoid speculative abstraction

## See also

- `tdd-reference.md`
- `software-design-principles.md`
