---
name: principle-modules-should-be-deep
description: Use when designing or reviewing a module, class, API, or abstraction, or when asked whether a layer, wrapper, or interface is worth keeping, even for a short snippet or a conceptual question, and even if the user does not mention depth, abstraction, or interfaces. Favors a simple interface hiding substantial functionality over shallow or pass-through code.
---

# Modules should be deep

A module = interface (everything a caller must know) + implementation (how it keeps the promise). Maximize functionality per unit of interface.

**Rule:** the interface must be simpler than the implementation. Cost is the interface; benefit is the functionality.

**Why:** callers should never need another module's implementation. Every extra detail in the interface raises cognitive load; every important detail left out creates obscurity (a false abstraction).

**Test:**
- Can a caller use it from its signature (name, parameter types, return type, errors) alone?
- Does it hide a decision callers would otherwise repeat?
- Would merging it into its only caller make the code simpler? Then it is shallow.

**Gotchas:**
- Many tiny classes or pass-through wrappers are shallow: the interface cost is paid, the hidden functionality is not.
- A deep module is not a deep call chain. A chain of layers scatters understanding; a deep module concentrates capability behind one interface.
- Do not omit details callers need (units, side effects, ordering). Hiding those is obscurity, not depth.

Source: John Ousterhout, *A Philosophy of Software Design*, 2nd ed.
