# Fullstack Seam-Splitting

## Contract/seam-first thinking

Use this route when one change crosses frontend and backend boundaries.

Treat the seam between them as the first design concern. Agree on the contract before filling in both sides.

## Define boundary first

Define the boundary in concrete terms:

- request shape
- response shape
- domain rule or workflow outcome
- error states
- loading or pending states if relevant
- ownership of validation and invariants

Keep the contract explicit so UI and backend can move independently behind it.

## Smallest vertical slice

Implement the thinnest end-to-end slice that proves the flow:

1. choose one user path
2. define the seam for that path
3. protect backend behavior at its owning boundary
4. protect frontend behavior at the visible boundary
5. connect them with the smallest passing integration

Avoid building all layers broadly before any path works end to end.

## Frontend/backend coordination

- use frontend behavior-first thinking on the UI side
- use backend TDD-first thinking on the backend side
- validate the seam with targeted integration or contract checks
- keep mapping and translation logic at the boundary, not smeared across both sides
- add loading, empty, and error handling deliberately when the seam affects visible state

When a fullstack change can be split, make one side stable enough for the other to depend on early.
