---
name: principle-foundational-thinking
description: Use before writing logic — choosing core types or data structures, sequencing scaffold versus feature work, deciding what concurrent actors share — when a design decision will shape everything built on it. Get the data shape and the foundations right first; downstream code becomes obvious.
---

# Foundational thinking

Structural decisions protect option value; code-level decisions protect simplicity. Get the foundations right before the work that leans on them.

**Rule:** get the data shape right before writing logic, do first whatever helps every later phase, and settle what concurrent actors share before they share it.

**Why:** the structure chosen first constrains everything built on it. The wrong data shape means logic compensates forever; the right shape makes the logic obvious. Scaffold is paid once and collected on every phase after.

**Test:**
- Trace the dominant access patterns first — do the core types fit them? "Show me your tables" before "show me your flowcharts."
- Does every later phase benefit from this existing? CI, lint, test infrastructure, and shared types are scaffold — do them first.
- If another actor modified this state concurrently, what happens? If not "nothing", isolate or serialize in the structure.
- Does this increment land a coherent abstraction, or spread a capability across callers as special-case coordination?

**Gotchas:**
- Converge types and data models, but DRY the structure, not every line — three similar statements beat a premature abstraction (see [principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)).
- Subtraction comes before scaffold: remove dead code, then lay foundations (see [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md)).
- Prefer explicit over clever — foundations are read far more than they are written.

Source: Fred Brooks, *The Mythical Man-Month* (tables over flowcharts); Rob Pike, "data dominates".
