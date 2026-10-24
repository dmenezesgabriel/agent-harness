---
name: principle-working-code-is-not-enough
description: Prefer a strategic mindset over tactical shortcuts, so the design improves with every change. Use when tempted to patch around a design problem, add a kludge to finish faster, or when choosing between the fastest fix and the cleanest design.
---

# Working code is not enough

**Rule:** the goal is a great design that also happens to work. Do not settle for working code that adds complexity.

**Tactical mindset (avoid):** finish the task fastest, with small kludges and shortcuts. Each looks fine alone and together they borrow time from the future (technical debt).

**Strategic mindset:** most code is written by extending a system, so your main job is to make future extensions easy. Invest a little extra now.

**Why:** complexity is incremental, so tolerate none (see `principle-avoid-complexity`). The best design emerges in small continual investments, not a big up-front design.

**Test:**
- Did I compare at least two designs and keep the cleanest?
- Is the next likely change easy in this design?
- Did I fix the design problem I found, or patch around it?

**Gotchas:**
- Fix a design problem when you find it, with a little extra time. Do not ignore it or work around it.
- Do not design the whole system up front. Improve in small steps, continually.

Source: John Ousterhout, *A Philosophy of Software Design*, 2nd ed.
