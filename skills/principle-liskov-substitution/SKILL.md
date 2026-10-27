---
name: principle-liskov-substitution
description: Use when a subclass refuses or weakens part of its parent's contract — overriding to throw, no-op, or narrow the result — when client code type-checks or switches on concrete subtypes, when asked whether an inheritance hierarchy or "is-a" relationship is sound, or when tests for the base contract need skips for a subtype, even for a short snippet or a conceptual question. Subtypes must be substitutable for their base type without surprising callers.
---

# Liskov substitution

If S is a subtype of T, code written against T must keep working — same contract kept — when handed an S. Substitution is about behavior, not the "is-a" shape of the data.

**Rule:** a subtype must honor the base contract — accept everything the base accepts, promise at least what the base promises, keep its invariants.

**Why:** every violation pushes knowledge of the subtype into the caller — an isinstance check, a try/except, a skipped test — and couples each caller to the hierarchy's special cases.

**Test:**
- Does an override strengthen preconditions (reject input the base accepted) or weaken postconditions (return less, throw where the base did not, mutate what the base kept immutable)?
- Does an override no-op or raise NotImplementedError? That is a refused bequest: the subclass inherited a promise it will not keep.
- Does client code switch on the concrete type? The hierarchy is leaking into its callers.
- Can the base contract's tests run against every subtype unmodified?

**Gotchas:**
- Square extends Rectangle is the classic trap: setWidth on a square silently changes height, breaking the base contract even though a square "is a" rectangle mathematically.
- Fix by narrowing the abstraction, splitting the hierarchy, or using composition — not by teaching callers about the exception.
- An empty or throwing override is almost never fine; shrink the base interface instead (see `principle-interface-segregation`).

Source: Barbara Liskov and Jeannette Wing, 1994; Robert C. Martin, *Agile Software Development*.
