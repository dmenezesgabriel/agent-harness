---
name: principle-tell-dont-ask
description: Use when code reads fields, attributes, getters, or keys from a value and then computes the decision itself, when the same rule is re-derived from one value's state in several places, when a record, struct, class, or dict carries data but its behavior lives in distant functions or services — an anemic model — or when reviewing where a piece of logic belongs, even for a short snippet or a conceptual question. Put the operation next to the data it works on — tell, don't ask.
---

# Tell, don't ask

Tell a value what you want done; do not ask for its state and decide for it. Code that reads another value's fields and computes with them is logic in the wrong place — feature envy.

**Rule:** an operation belongs next to the data it operates on. Callers tell; they never ask.

**Why:** every asker re-derives a decision the value already owns, so the rule scatters into every caller — change amplification. Callers couple to the value's internal shape, and the value degenerates into an anemic model: a data bag whose behavior lives everywhere except with the data.

**Test:**
- Does this code read fields, getters, attributes, or keys from one value, then compute a decision? That computation is envious — move it onto the value.
- Would a method like `order.eligible_for_discount()` delete the same derivation at every call site?
- Is a struct, record, or dict manipulated mostly by functions that live far from it? Its behavior belongs with it.

**Gotchas:**
- Accessors that answer a real domain question are fine; the smell is asking questions and then doing the value's job.
- Envy is about the value's own rules: mapping, filtering, and grouping in a pipeline are the pipeline's work, not the element's.
- Anemic does not mean "no methods exist" — a value whose methods are all accessors is still a data bag.
- In dataflow and functional code, ask whether the rule belongs to the value or to the pipeline stage; do not bury pipeline decisions inside the data type (see [principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)).

Source: Jeff Bay, Object Calisthenics (no getters/setters); Martin Fowler, "Tell Don't Ask" and feature envy; *refused bequest* of logic to data-less services.
