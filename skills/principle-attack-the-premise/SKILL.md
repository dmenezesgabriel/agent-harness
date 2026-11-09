---
name: principle-attack-the-premise
description: Use when two or more fixes that share one assumption have failed the same gate, when debugging stalls on repeated failed fixes, or when every attempted fix assumes the same cause. Write the premise down and test it directly before writing another fix that assumes it.
---

# Attack the premise

When two or more fixes that share one premise have failed the same gate, suspect the premise, not the fixes. Each failed fix is evidence against the belief it assumed; another fix on the same premise spends effort where the evidence already says the cause is not.

**Rule:** write the premise down in one sentence and test it directly before the next fix.

**Why:** a fix treats what it assumes as fact. When the shared assumption is wrong, every fix built on it is a coincidence that happens not to work — and the repeated failures are data about the premise, not about the fixes.

**Test:**
- Can you say the premise in one sentence — the belief every failed fix shared?
- What observation would come out differently if it were false? Make that observation.
- If the evidence contradicts the premise: what do the failures share that it did not predict? Look there next (see [principle-fix-root-causes](../principle-fix-root-causes/SKILL.md)).
- If it confirms the premise: the earlier fixes treated a consequence, not the cause — ask the next why.

**Gotchas:**
- Watch how the failures are distributed, not only how large they are.
- Remove the condition rather than compensate for it — a mechanism that cleans up after an imbalance leaves the cause in place.
- Do not start the next fix until the premise is written down and tested.

Source: David J. Agans, *Debugging*; Karl Popper, falsifiability.
