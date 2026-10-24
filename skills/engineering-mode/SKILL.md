---
name: engineering-mode
description: Use when designing, sketching, changing, or reviewing a module, class, API, or interface, and at the start of any feature, bug fix, or refactor. Routes the task to the matching principles and checks before code is written or judged, even if the user does not mention architecture or principles.
---

# Engineering mode

Load the skill for your situation before you design, change, or review code:

| Situation | Load |
|---|---|
| Defining or reviewing a module, class, layer, or public interface | `principle-modules-should-be-deep` |
| A Python wrapper, adapter, or service layer | `find-pass-through-functions`, then judge each finding with `principle-modules-should-be-deep` |
| One change needs edits in many places, or hidden knowledge to make safely | `principle-avoid-complexity` |
| Choosing between a quick patch and fixing the design | `principle-working-code-is-not-enough` |

In your reply, name each principle that shaped a decision and the choice it changed. Cite only principles you loaded.
