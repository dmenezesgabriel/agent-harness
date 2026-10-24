---
name: principle-modules-should-be-deep
description: Design modules, classes, and functions with a simple interface hiding substantial functionality. Use when designing or reviewing a new module boundary, public API, or abstraction, or when code feels shallow, pass-through, or hard to use without reading its implementation.
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
