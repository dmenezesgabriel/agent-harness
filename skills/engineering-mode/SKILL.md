---
name: engineering-mode
description: Entry point for non-trivial software work such as a new feature, bug fix, refactor, design, or code review. Routes the task to the matching principles and checks before code is written or judged. Use at the start of any task that changes or reviews code beyond a trivial edit, even if the user does not mention architecture or principles.
---

# Engineering mode

Load the skill for your situation before you design, change, or review code:

| Situation | Load |
|---|---|
| Defining a module, class, or public interface | `principle-modules-should-be-deep` |
| Reviewing a wrapper, adapter, or service layer in Python | `find-pass-through-functions`, then judge each finding with `principle-modules-should-be-deep` |

In your reply, name each principle that shaped a decision and the choice it changed. Cite only principles you loaded.
