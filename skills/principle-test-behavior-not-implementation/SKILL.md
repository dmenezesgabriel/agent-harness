---
name: principle-test-behavior-not-implementation
description: Use when writing, changing, reviewing, or deleting a test, when tests break on refactor though behavior stayed the same, or when a suite passes while the feature is broken. Assert what the code's users can observe through the interface they use — no more, no less.
---

# Test behavior, not implementation

Behavior is what the code's users — a caller, an end user, another service — can observe through the interface they use: return values, errors, readable state, effects on the outside. Implementation is what they cannot see: private helpers, internal call order, which collaborator did the work.

**Rule:** assert what users can observe, so the test fails when that behavior breaks and survives every change that leaves behavior intact.

**Why:** a test pinned to internals must be rewritten on every refactor while catching no bug — it costs like a test and protects like a comment. A test looser than the contract passes while the feature is broken — protection with no teeth.

**Test:** judge each test by two imagined edits.
- Break the behavior — wrong value, skipped effect. If the test still passes, it proves nothing. Usual causes: assertion looser than the contract, expected value computed by the code under test, assertion on data the test built itself.
- Change the internals — same observable results, new structure. If the test now fails, it pins the implementation.

**Gotchas:**
- The contract decides, not the shape of the assertion: that a mocked external service received no charge call is behavior — the service can observe it; that an internal helper ran is implementation.
- An exact error message pins wording no caller reads; the error type callers branch on is the contract.
- An invariant — a key present in two tables, a compile-time guarantee — is behavior too.

Source: Kent Beck, "Test Desiderata" (tests insensitive to structure); Google Testing Blog.
