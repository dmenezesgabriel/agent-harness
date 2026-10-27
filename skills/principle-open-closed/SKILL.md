---
name: principle-open-closed
description: Use when adding a new variant, case, format, or integration means editing existing working code — a growing switch, if/elif chain, registry, or dispatch — when choosing between modifying tested code and adding new code, or when designing plugin or extension points, even for a short snippet or a conceptual question. Extend behavior by adding code, not by changing code that already works.
---

# Open–closed

A module should be open for extension but closed for modification: a new behavior is born as new code, not as an edit to code that already works.

**Rule:** close the module against the axis of change that actually varies; leave everything else open.

**Why:** every edit to working code risks the callers it already serves, forces retesting, and mixes a new decision into old ones. An extension point turns "add a variant" from surgery into a new file.

**Test:**
- Does adding the next variant touch a file that already works? If yes, that file is not closed against this axis of change.
- Is there a switch, if/elif chain, or type check that grows a branch per variant? Hide the dispatch behind one interface and register the variants.
- Can a third party add a case without editing the core? That is a plugin.

**Gotchas:**
- Closure is strategic, not total: pick the axes that actually recur. You cannot be closed against every change, and trying is needless complexity.
- The second variant usually earns the abstraction; do not build a plugin system for a case that may never come.
- One registry or strategy table beats a dispatch scattered across files.

Source: Bertrand Meyer, *Object-Oriented Software Construction*; Robert C. Martin, *Agile Software Development*.
