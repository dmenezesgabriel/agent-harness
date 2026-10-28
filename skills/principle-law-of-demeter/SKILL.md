---
name: principle-law-of-demeter
description: Use when callers chain through several objects to reach what they need — a.b.c.d, foo().bar().baz(), or deep key paths like cfg["db"]["pool"]["size"] — when a change to one link's structure keeps breaking distant callers, when reviewing train-wreck expressions, or when deciding where a traversal should live, even for a short snippet or a conceptual question. Talk only to your immediate friends — ask the neighbor for the outcome, never reach through it.
---

# Law of Demeter

Talk only to your immediate friends: code may use the values it holds, its parameters, and what it creates — never their internals. `order.get_customer().get_address().get_city()` is a train wreck: one reach through three objects' structures.

**Rule:** one dot of reach per line is the exercise form; the doctrine is — do not traverse other values' internals. Ask your direct collaborator for the outcome.

**Why:** each extra hop couples the caller to every link's structure. Rename `address` and every traversal in every caller breaks — the caller learned three structures to fetch one value (hidden dependencies; see `principle-avoid-complexity`).

**Test:**
- Count the hops: `a.b.c.d`, `foo().bar().baz()`, `x["a"]["b"]["c"]`. More than one reach is a violation.
- Does the caller know the path, or does it ask the neighbor for the result? Move the traversal to whoever owns the first hop — `report.billing_city()`.
- Deep key paths into data documents count too: `cfg["db"]["pool"]["size"]` couples the reader to the document's shape; put access behind one function owned next to the format.

**Gotchas:**
- Fluent APIs and builders chain on the same value — `query.where(...).order_by(...)` returns the same friend, not strangers.
- Compositions where each step returns the caller's own type (pipelines, map/filter, monadic binds) are not train wrecks — the type never changes hands.
- The fix is not sprinkling `get_city()` on every link — that moves the chain, not the knowledge. Put the *outcome* on the nearest collaborator (see `principle-tell-dont-ask`).

Source: Law of Demeter, Northeastern University 1987; Jeff Bay, Object Calisthenics (one dot per line).
