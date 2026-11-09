---
name: principle-prove-it-works
description: Use before declaring a task done, when reporting that something works, when verifying a change, or when the only evidence is a proxy — it compiled, no errors printed, a self-report. Check the real artifact directly and keep output a reviewer can rerun.
---

# Prove it works

Unverified work has unknown correctness. Verify the real artifact directly — run the feature, read the actual value, inspect the diff — never a proxy: not "it compiled", not "no errors printed", not a self-report.

**Rule:** before declaring done, observe the real thing and show the evidence, not a claim.

**Why:** proxies feel cheaper than direct observation and are wrong often enough to cost more. Acting on a wrong inference compounds — the next change builds on a base nobody checked.

**Test:**
- Did you run the artifact itself, or infer from something near it? File mtimes, cached output, and logs that say "done" are proxies.
- Can a reviewer re-run your check? The strongest proof is a small script that re-runs the same comparison, kept with its output.
- When verification fails, suspect the observation method before the system.

**Gotchas:**
- "The tests pass" proves the tests, not the feature — run the feature when the claim is about the feature.
- Green is not safe: a check that cannot fail never measured anything (see [principle-test-behavior-not-implementation](../principle-test-behavior-not-implementation/SKILL.md)).
- Each check belongs at the end of a unit of work, not deferred to the end of the batch (see [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md)).

Source: Andy Hunt & Dave Thomas, *The Pragmatic Programmer* ("don't assume it — prove it").
