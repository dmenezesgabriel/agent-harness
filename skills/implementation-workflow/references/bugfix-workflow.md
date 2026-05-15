# Bugfix Workflow

## Reproduce first

Do not start by guessing.

Make the bug happen reliably through:

- a failing test
- a scriptable repro
- a minimal manual path when automation is not yet possible

State the observed behavior and the expected behavior clearly.

## Regression protection

Add protection before or with the fix.

Prefer a regression test at the highest stable boundary that can prove the bug without coupling to internals.

If the area is risky or poorly understood, add characterization coverage around nearby behavior first. State the invariant or user-visible contract the fix is meant to restore so the test protects the right thing.

## Smallest corrective change

Fix only what is needed to correct the behavior.

Keep the change narrow:

1. reproduce
2. add regression protection
3. implement the smallest fix
4. rerun the repro and targeted checks

## Avoid opportunistic cleanup

Do not mix broad refactors, redesign, renames, or architectural cleanup into the bugfix unless they are required for safety.

If cleanup is worthwhile, protect the bug first and treat the cleanup as a separate follow-up step.
