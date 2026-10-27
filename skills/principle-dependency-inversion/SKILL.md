---
name: principle-dependency-inversion
description: Use when business logic creates, imports, or knows about infrastructure — databases, HTTP clients, frameworks, file formats — when core code cannot be unit-tested without external services or heavy mocking, when deciding where an interface should live or which direction a dependency should point, or when layering policy against mechanism, even for a short snippet or a conceptual question. High-level policy should not depend on low-level details; both depend on abstractions owned by the policy.
---

# Dependency inversion

High-level policy must not depend on low-level detail. The dependency arrow points from detail toward policy: infrastructure implements the interface the policy defines. That is ports and adapters.

**Rule:** the policy declares the port it needs — an interface owned by the caller, living in the policy's own package — and details plug in behind it.

**Why:** details (DB, HTTP, frameworks, file formats) change faster than policy. When policy depends on detail, every detail change ripples into the code that matters most, and the core cannot be tested or reasoned about alone.

**Test:**
- Does domain code `new` up or import a database, HTTP client, or framework? The arrow points the wrong way.
- Can the core logic be unit-tested with no network, disk, or DB? If not, a port is missing.
- Where does the interface live? In the adapter's package, the policy still depends on the detail. In the policy's package, the dependency inverts — the Hollywood principle: don't call us, we'll call you.

**Gotchas:**
- Dependency injection is one way to wire it, not the principle. You can inject concretions and invert nothing; what matters is which direction the source-code dependency points.
- The interface belongs to the client (the policy), not to the implementer (see `principle-interface-segregation`).
- Invert at boundaries that matter; a stable detail used by everything can stay concrete (see `principle-avoid-complexity`).

Source: Robert C. Martin, *Agile Software Development*; *Clean Architecture*. Ports and adapters: Alistair Cockburn.
