---
name: principle-sequence-verifiable-units
description: Use for multi-step work — sweeps, migrations, runs of similar edits — when stacking commits or PRs, or when a batch of changes is hard to review or bisect. Break work into small units that each end in a check, verify each before the next, and order delivery so the sequence proves itself.
---

# Sequence work into verifiable units

Multi-step work is a sequence, not a batch. Each unit ends in a state you can check; do not advance until the current one is green.

**Rule:** break the work into the smallest units that each end verifiable, check each before the next, and order delivery so the sequence proves itself to a reviewer.

**Why:** a break caught at the unit that caused it is cheap to localize; caught after a batch it is buried, and you have already built on a broken base. Sequencing delivery the same way turns "trust me" into something a reviewer can replay.

**Test:**
- Can you name the check that ends the current unit — a test run, a command, a diff inspection?
- Is each commit green on its own? Rebase onto clean trunk first so each check measures the real baseline.
- Does the sequence read as an argument: failing test before fix, removal before reshape, baseline before treatment, scaffold before feature?

**Gotchas:**
- When a tool makes the edits, the per-unit check is nearly free — run it anyway; the cheap check is the point.
- A unit too big to check in one step is two units.
- Each check must be real, not a proxy (see [principle-prove-it-works](../principle-prove-it-works/SKILL.md)); the first unit is often a subtraction (see [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md)).

Source: Kent Beck, extreme programming (small steps); continuous-integration practice.
