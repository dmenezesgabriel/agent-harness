---
name: principle-fix-root-causes
description: Use when debugging a bug, error, or failure that keeps returning, when a fix only moved the symptom, when tempted to add a guard, retry, or null check where something broke, or when deciding where a fault belongs. Trace each symptom to the first place the system went wrong and fix it there.
---

# Fix root causes

The symptom is where a wrong state became visible; the root cause is the first place the system did what it should not, or failed to handle a state it must. Fix the fault, not the place it surfaced.

**Rule:** trace each symptom back to the first wrong decision in the code and fix it there.

**Why:** a fix at the symptom hides the evidence and leaves the fault free to surface elsewhere. Each symptom-patch is a workaround for a bug nobody named — the system gets harder to reason about and no safer.

**Test:**
- Reproduce first — if you cannot make it fail, you cannot prove the fix worked.
- Ask why at each step until the answer is a wrong decision, not a consequence of an earlier one.
- Is the state that broke it legitimate? If the system may reach that state, handling it is the fix; if it should never exist, a guard where it broke hides the bug — find what produced it.
- Does this fault exist elsewhere? Fix the pattern, not the instance.

**Gotchas:**
- Guards, retries, swallowed errors, and clamped values are the usual hiding places — suspect them, do not trust them.
- Failures that appear only after restart usually mean persisted state: config, caches, locks.
- A workaround that needs a paragraph of justification means the code is wrong, not the comment.
- When fixes keep failing on the same assumption, question the assumption itself (see [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md)).

Source: David J. Agans, *Debugging*; Andy Hunt & Dave Thomas, *The Pragmatic Programmer*.
