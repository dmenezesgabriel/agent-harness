---
name: engineering-mode
description: Use when designing, sketching, changing, or reviewing a module, class, API, or interface, when asked for design advice or whether a structure is worth keeping or restructuring, and at the start of any feature, bug fix, or refactor. Routes the task to the matching principles and checks before code is written or judged, even if the question is conceptual or the user does not mention architecture or principles.
---

# Engineering mode

## 1. Classify

Pick the task type first. It decides everything after.

| Task | Do |
|---|---|
| **Question**: explain, compare, how or why something works | Answer from evidence. Load no principle unless the question is about a design. |
| **Change**: feature, bug fix, refactor, design, review | Run the phases below. |

## 2. Phases

Open a checklist with these steps. A step you skip stays listed as `skip: <reason>`.

1. **Work**: smallest change that solves the problem; run it or test it.
2. **Right**: apply each principle whose situation fits; run each check that fits.
3. **Prove**: show the evidence (test or command output), not a claim.

## 3. Principles

Apply when the situation fits. Load the named skill before you cite it.

- **Modules should be deep** ([principle-modules-should-be-deep](../principle-modules-should-be-deep/SKILL.md)). Defining or reviewing a module, class, layer, or interface. Simple interface, substantial hidden functionality.
- **Hide information** ([principle-hide-information](../principle-hide-information/SKILL.md)). Callers must know an implementation decision — format, ordering, backend — to use a module, or one design change would edit many modules. The interface reveals outcomes, never decisions.
- **Avoid complexity** ([principle-avoid-complexity](../principle-avoid-complexity/SKILL.md)). One change needs edits in many places, or hidden knowledge to make safely. One decision in one place; obvious names and units.
- **Working code is not enough** ([principle-working-code-is-not-enough](../principle-working-code-is-not-enough/SKILL.md)). Choosing between a quick patch and fixing the design. Fix the design problem you find.
- **Single responsibility** ([principle-single-responsibility](../principle-single-responsibility/SKILL.md)). A module serves more than one actor or is edited for unrelated reasons. One reason to change per module.
- **Open–closed** ([principle-open-closed](../principle-open-closed/SKILL.md)). A new variant means editing working code — a growing switch or dispatch. Extend by adding code.
- **Liskov substitution** ([principle-liskov-substitution](../principle-liskov-substitution/SKILL.md)). A subtype refuses or weakens its base contract; callers switch on concrete types. Subtypes must substitute.
- **Interface segregation** ([principle-interface-segregation](../principle-interface-segregation/SKILL.md)). Implementers stub out unused methods, or one client's change hits every client. Split interfaces per role.
- **Dependency inversion** ([principle-dependency-inversion](../principle-dependency-inversion/SKILL.md)). Policy imports or builds infrastructure; the core cannot be tested alone. Depend on abstractions the policy owns.
- **Tell, don't ask** ([principle-tell-dont-ask](../principle-tell-dont-ask/SKILL.md)). Callers compute from another value's fields; behavior drifted away from its data. Move the operation next to the data.
- **Law of Demeter** ([principle-law-of-demeter](../principle-law-of-demeter/SKILL.md)). Callers chain through values to reach a result — train wrecks, deep key paths. Ask the neighbor for the outcome.
- **Domain types over primitives** ([principle-domain-types-over-primitives](../principle-domain-types-over-primitives/SKILL.md)). Meaning travels in bare primitives; swaps and re-validation at call sites. Parse once into named types.
- **Flat methods** ([principle-flat-methods](../principle-flat-methods/SKILL.md)). Control flow nests into arrows and if/elif chains. No else: guard clauses, early returns, dispatch.

## 4. Checks

- **Pass-through functions** ([find-pass-through-functions](../find-pass-through-functions/SKILL.md)). A wrapper, adapter, or service layer. Judge each finding with [principle-modules-should-be-deep](../principle-modules-should-be-deep/SKILL.md).
- **Nested branches** ([find-nested-branches](../find-nested-branches/SKILL.md)). Functions with else/elif or control flow nested past one level. Judge each finding with [principle-flat-methods](../principle-flat-methods/SKILL.md).
- **Train wrecks** ([find-train-wrecks](../find-train-wrecks/SKILL.md)). Chains reaching through three or more links. Judge each finding with [principle-law-of-demeter](../principle-law-of-demeter/SKILL.md).
- **Feature envy** ([find-feature-envy](../find-feature-envy/SKILL.md)). Functions reading several attributes of one foreign value. Judge each finding with [principle-tell-dont-ask](../principle-tell-dont-ask/SKILL.md).

## Reply

Name each principle that shaped a decision and the choice it changed. Cite only principles you loaded.
