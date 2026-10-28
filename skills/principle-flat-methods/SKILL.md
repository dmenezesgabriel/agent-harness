---
name: principle-flat-methods
description: Use when a method or function's control flow nests — if/elif/else chains, arrow-shaped or pyramid code, loops wrapping branches — when refactoring toward early returns or guard clauses, when deciding how to structure conditional logic, or when a change means adding one more arm to a deep branch, even for a short snippet or a conceptual question. No else and no elif — guard the edges and keep the happy path flat on the left margin.
---

# Flat methods

A method should read as a straight line, not an arrow. The exercise rule: **never write `else` or `elif`** — early returns and guard clauses handle the edges, and the happy path stays on the left margin.

**Rule:** every `if` either exits early (a guard clause) or delegates the branch — a dispatch table, polymorphism, a pipeline step. An `else` is a missed early return; an `elif` is a missed dispatch.

**Why:** nesting is additive cognitive load — to read the last line you must hold every enclosing condition in your head. `else` says "this runs when some earlier test failed": a hidden dependency between distant lines. Arrow code buries the point of the method in its deepest corner.

**Test:**
- Can you read the main case from the left margin without unwrapping conditions?
- Does every `if` either bail out or select a mechanism? Any `else` or `elif` violates the rule.
- After flattening, does the method keep at most one level of indentation? Extract what still nests into a named function.

**Gotchas:**
- The guard-clause idiom — `if bad: return` repeated at the top, or `if err != nil: return err` — is the pattern itself, not a violation: it reads flat.
- Inverting a condition to delete `else` is the mechanic, not the goal. If the result is still a decision tree, extract the branches or replace the chain with a lookup table.
- Sometimes a boolean expression beats a small `if` (`return ok and x`); pick whichever form reads flatter.
- A single `if/else` expressing one symmetric fork is the boundary case — the exercise still says remove it; judgment says a ternary-level choice may read simpler (see `principle-avoid-complexity`).

Source: Jeff Bay, Object Calisthenics (don't use ELSE, one level of indentation); guard clause / bouncer pattern; "never nesters".
