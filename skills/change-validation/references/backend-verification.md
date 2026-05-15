# Backend Verification

Use this reference when the change affects rules, services, APIs, persistence, or other server-side behavior.

Confirm the smallest set that proves the changed behavior is correct.

## Check for
- domain rules and invariants
- validation and error handling, including rejected inputs and failure paths
- authorization, trust boundaries, and assumptions about caller-controlled data
- request, response, event, or schema contracts
- persistence behavior, transaction boundaries, and rollback behavior when relevant
- idempotency, concurrency, and migration safety when the change can affect them

## Practical rules
- start with targeted tests for the changed rule or seam
- add integration coverage when storage, transactions, handlers, queues, or external boundaries are involved
- verify both success and denied or invalid paths when permissions or validation changed
- include type, build, or schema-generation checks when the toolchain depends on them
- do not broaden into unrelated hardening unless the task or risk clearly requires it
