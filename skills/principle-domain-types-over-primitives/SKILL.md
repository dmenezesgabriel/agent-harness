---
name: principle-domain-types-over-primitives
description: Use when meaning travels in bare primitives, strings, dicts, or tuples — parameters of the same primitive type getting swapped, validation or unit interpretation repeated at call sites, ids, money, emails, or ranges passed as raw values — when designing function signatures or domain models, when asked how to stop type-confusion or stringly-typed bugs, or when deciding whether a value deserves its own type, even for a short snippet or a conceptual question. Wrap domain values in named types; parse once at the boundary, then trust the type.
---

# Domain types over primitives

A value that means something — an email, a user id, money, a range — should not travel as a bare primitive. Primitive obsession passes meaning in the variable's name and hope; a domain type carries it in the value.

**Rule:** wrap domain values in types named for what they are — a value object, a newtype, a branded type, a validated record. Parse into them once at the boundary, then trust the type inside: parse, don't validate.

**Why:** bare primitives mix freely — `int` quantity swaps with `int` price silently. Rules about the value scatter: every site re-validates, re-formats, re-interprets units — change amplification (see `principle-avoid-complexity`). A domain type makes illegal values unconstructible and gives those rules one home.

**Test:**
- Do two parameters share a primitive type but mean different things? That is a swap bug waiting — brand each.
- Is the same validation, format, or unit interpretation repeated at call sites? It belongs in the type's construction.
- Does a bare dict or tuple stand in for a concept? Name it and give it a parser.

**Gotchas:**
- No compiler required: in dynamic languages, enforce at construction — a factory or parse function that rejects bad values — and treat raw input as untyped until parsed. The discipline is identical; only the enforcement point moves.
- A one-off, single-use value stays primitive; the rule bites when meaning recurs or correctness matters (money, ids, emails, units, ranges).
- A bare collection with its rules scattered over callers is the same smell — a first-class collection (one type owning the list plus its operations) is the same fix (see `principle-tell-dont-ask`).

Source: Jeff Bay, Object Calisthenics (wrap all primitives); Alexis King, "Parse, don't validate"; Martin Fowler, value object.
