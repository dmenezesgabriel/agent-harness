---
name: principle-avoid-complexity
description: Use when a change would touch many files or places, when code is hard to change safely, when asked how to restructure it, or when names, units, or constants are unclear. Apply even if the user never mentions complexity, coupling, or design, including for conceptual questions. Keeps a system obvious by cutting dependencies and obscurity, with zero tolerance for each small increment of complexity.
---

# Avoid complexity

Complexity is whatever makes a system hard to understand or modify. Spot it by three symptoms, fix it at two causes.

**Symptoms:**
- **Change amplification:** one simple change needs edits in many places.
- **Cognitive load:** how much a developer must know to finish the task.
- **Unknown unknowns:** it is not obvious what must change, or what to know. The worst one, since bugs reveal it late.

**Causes:**
- **Dependencies:** code that cannot be understood or changed alone.
- **Obscurity:** important information is not obvious.

**Rule:** make the system obvious. Fewer dependencies, and the remaining ones simple and explicit. Names and constants carry their meaning and units.

**Why:** complexity grows in small increments and is hard to remove once it accumulates. Each increment counts, so accept none.

**Test:**
- Does each design decision live in one place? If it changes, how many files change?
- Can a newcomer find what to modify without already knowing?

**Gotchas:**
- Needing heavy documentation to explain code is a red flag the design is off. Simplify first.
- Share constants and values from one central place instead of repeating them.

Source: John Ousterhout, *A Philosophy of Software Design*, 2nd ed.
