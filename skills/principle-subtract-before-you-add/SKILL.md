---
name: principle-subtract-before-you-add
description: Use when sequencing an addition, refactor, or rewrite, when the target area carries dead paths, unused validators, or abandoned stubs, or when deciding whether to build on top of existing complexity. Remove first, then build on the simpler base.
---

# Subtract before you add

When evolving a system — an addition, a refactor, a rewrite — remove first, then build. Dead code, redundant validators, abandoned stubs, and speculative guards all tax every change built on top of them.

**Rule:** sequence removal before construction; build on the simpler base and leave it simpler than you found it.

**Why:** every line kept is paid on every read, every change, every check. Complexity removed before the build shrinks the surface the new work must fit — and the deletion itself often reveals the design the addition actually needed.

**Test:**
- What can be deleted before this change lands — dead paths, unused parameters, guards for states that cannot occur?
- Would removing the complication change the design you were about to add? Subtract first and find out.
- Is the new code built on the smaller surface, or pasted onto the old one?

**Gotchas:**
- Cut before you polish — get to the minimum before investing in code that may not survive.
- Design for observed usage, not speculative edge cases; a validator with no reachable failure is complexity, not safety (see [principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)).
- Confirm the thing is unused or unreachable before deleting — subtraction is verified removal, not guessing.

Source: John Ousterhout, *A Philosophy of Software Design* (increments of complexity); the boy-scout rule.
