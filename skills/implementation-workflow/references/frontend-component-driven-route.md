# Frontend Component-Driven Route

## When to use

Use this route when the main change is user-visible:

- component behavior
- interaction or form behavior
- rendering states
- navigation or screen composition
- accessibility fixes
- reusable UI building blocks

## User-visible behavior first

Define the behavior in terms of what the user can see, trigger, and verify.

Start from scenarios, acceptance criteria, or concrete state examples before changing component internals. Given/When/Then-style examples are useful when a flow or state transition needs to stay concrete.

## State modeling

List the important states up front, such as:

- default
- loading
- success
- empty
- error
- disabled
- invalid
- expanded or selected

Make states explicit instead of spreading them across unrelated flags.

## Accessibility as contract

Treat accessibility as part of the expected behavior:

- semantic role
- accessible name or label
- keyboard operation
- focus behavior
- error communication

Test what assistive technology and keyboard users rely on, not just visual output.

## Isolation and composition

Build the smallest useful component or composition boundary first.

- verify behavior in isolation where possible
- keep side effects at the boundary
- mock network, time, storage, and browser APIs at their edges rather than mocking the component under test
- compose into larger screens after the component contract is clear
- prefer composition over large prop surfaces

## See also

- `component-driven-design.md`
