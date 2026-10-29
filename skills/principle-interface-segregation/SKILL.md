---
name: principle-interface-segregation
description: Use when implementers stub out, throw on, or no-op methods they do not need, when an interface or base class has grown fat, when a change for one client forces recompiles or retesting of unrelated clients, or when designing interfaces shared by different client roles, even for a short snippet or a conceptual question. No client should be forced to depend on methods it does not use.
---

# Interface segregation

Clients should not be forced to depend on methods they do not use. Split fat interfaces into role interfaces, each sized for one client's use.

**Rule:** an interface belongs to its client, not its implementer. Give each client role the smallest interface that serves it.

**Why:** every unused method on an interface is a dependency the client never asked for — it couples the client to changes made for other clients, forces stub implementations, and makes mocks and adapters carry dead weight.

**Test:**
- Do implementers raise NotImplementedError, return null, or no-op on parts of the interface? That part belongs to a different role interface.
- Do mocks or adapters implement only a fraction of the methods? Count the fraction.
- Does a change requested by one client force changes or retesting in clients that never call that method?

**Gotchas:**
- A header interface lists everything one class can do; a role interface names what one client needs. Prefer role interfaces, named for the client's use (ReadsConfig, RoutesRequests).
- Two thin interfaces on one implementation are normal and cheap; one fat interface is the expensive default.
- Segregate by real client roles, not arbitrarily — each split should map to an actual client need (see [principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)).

Source: Robert C. Martin, *Agile Software Development*; *Clean Architecture*.
