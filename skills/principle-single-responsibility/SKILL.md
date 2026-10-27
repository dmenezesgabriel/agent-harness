---
name: principle-single-responsibility
description: Use when a class or module accumulates unrelated duties, when one file gets edited for unrelated reasons or by different teams, when deciding where a responsibility belongs, when asked whether to split a module or review a god object, even for a short snippet or a conceptual question, and even if the user does not mention cohesion, actors, or design. A module should have one, and only one, reason to change.
---

# Single responsibility

A responsibility is a reason to change, and a reason to change is an actor: the person or group whose requests the module serves. Gather together what changes for the same actor; separate what changes for different actors.

**Rule:** a module should be responsible to one, and only one, actor.

**Why:** when two actors share a module, a change for one can break what the other depends on, and every change needs coordination — merge collisions, retesting of unrelated behavior. Splitting by actor gives each change a small blast radius.

**Test:**
- List the actors who can ask this module to change. More than one means split it.
- Would a change for actor A force retesting the code actor B cares about?
- Check for accidental duplication: two things that merely look alike but change for different actors get merged, and the merge couples the actors.

**Gotchas:**
- A god object is many responsibilities under one name — the extreme violation.
- The test is the actor count, not the line count. One function doing three steps for one actor can be cohesive.
- Splitting where there is only one actor creates needless layers (see `principle-avoid-complexity`).

Source: Robert C. Martin, *Clean Architecture*; *Agile Software Development: Principles, Patterns, and Practices*.
