---
name: principle-hide-information
description: Use when deciding what a module's interface should reveal, when callers must know an implementation decision — data format, storage backend, call ordering, concurrency strategy — to use the module, when one design change would force edits in many modules, or when choosing what to keep out of an API, even for a short snippet or a conceptual question. Hide each decision likely to change inside one module; let the interface expose outcomes, never decisions.
---

# Hide information

A module encapsulates a few design decisions — knowledge embedded in its implementation but absent from its interface. Choose what to hide by what is likeliest to change.

**Rule:** the interface must not reveal a decision callers would have to know or repeat to use the module — data structures, algorithms, formats, ordering, backends.

**Why:** a decision that escapes the interface is relearned by every caller. When the decision changes, every place holding it edits — information leakage, the mechanism behind "one change, many edits" (see [principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)). Leaks also inflate the interface, making the module shallower (see [principle-modules-should-be-deep](../principle-modules-should-be-deep/SKILL.md)).

**Test:**
- Pick a decision: storage engine, wire format, hash algorithm, retry policy. If it changed, which modules edit? More than one — the decision is leaking.
- Can a caller use the module from its signature alone, without knowing how the inside works?
- Temporal knowledge is information too: "call `init` before `get`", "close after open" — a required ordering is a decision the interface failed to hide.

**Gotchas:**
- Hiding means hiding *decisions*, not stuffing code inside: a large module whose interface still exposes a format or an ordering leaks.
- Do not hide what callers genuinely need — results, units, errors they must handle. Hiding those is obscurity, not information hiding.
- Not every decision deserves hiding. Hide the ones likely to change; a stable decision costs little to reveal.

Source: David Parnas, *On the Criteria to Be Used in Decomposing Systems into Modules*, CACM 1972; John Ousterhout, *A Philosophy of Software Design*, 2nd ed., ch. 5.
