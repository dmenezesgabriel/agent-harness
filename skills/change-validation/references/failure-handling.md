# Failure Handling

When validation fails, classify the signal before changing code.

## Failure types

### Change-caused
- introduced by the current change
- fix within approved scope
- add or adjust regression coverage when needed

### Pre-existing
- already broken before this change or clearly unrelated
- do not silently absorb the issue into the current work
- report it as residual risk or a follow-up item

### Flaky
- non-deterministic or environment-dependent
- rerun the smallest sufficient check to confirm the signal
- report the flake instead of pretending the result is stable

### Expected
- failure caused by an intentional behavior change
- update the affected test, fixture, snapshot, or contract only when the new behavior is approved

## Working rules
- fix only what is within approved scope
- rerun the smallest sufficient set after each fix
- expand the check set only if failures show the original validation was not enough
- do not change unrelated behavior just to make checks pass
- avoid opportunistic cleanup, refactors, or side fixes unless explicitly approved
- escalate only when the needed fix requires a new product, policy, or architecture decision
