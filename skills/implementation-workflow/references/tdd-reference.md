# Test-Driven Development Reference

## Purpose

Use this reference as a quick guide when the implementation route is TDD-first.

Goal: move in very small steps — write a failing test, make it pass with the smallest change, then refactor while tests stay green.

## Core Loop

1. **Red** — write one small test for one behavior and watch it fail.
2. **Green** — make it pass with the smallest correct change.
3. **Refactor** — improve names, structure, or duplication only while all tests are green.
4. Repeat.

## Practical Rules

- **One behavior at a time** — do not bundle multiple expectations into one step.
- **Use the smallest failing example** — start from the simplest concrete case that proves the behavior.
- **Characterize before risky changes** — when existing behavior is unclear but must be preserved, add a characterization test first.
- **Test behavior, not structure** — prefer public contracts, rules, and observable outcomes over private methods or internal call order.
- **Run tests frequently** — after the new test, after the small implementation step, and after refactors.
- **Refactor only on green** — do not mix behavior changes with structural cleanup.

## Common TDD Moves

### Test First
Write the test before production code so the next step is driven by behavior.

### Assert First
Start by writing the expected assertion or result, then fill in the setup needed to reach it.

### Fake It
Return a simple hard-coded value or direct shortcut first if that is the fastest safe step to green.

### Triangulate
When one example could be solved by a fake, add another example that forces a more general implementation.

### Obvious Implementation
If the implementation is truly straightforward, write the direct solution after the failing test instead of taking extra micro-steps.

## What Not To Do

- Do not write large tests covering many behaviors at once.
- Do not write production code without a failing test driving it.
- Do not keep coding after green when the next step should be a refactor or a new test.
- Do not refactor while tests are failing.
- Do not couple tests tightly to internal structure when the behavior can be checked through a clearer boundary.
- Do not introduce ports, mocks, or seams that only mirror the current implementation with no real boundary need.

## Short Examples

### Small failing example

```text
Test: empty cart total is 0
Run tests -> fails
Implement: total([]) = 0
Run tests -> passes
Refactor -> none needed
```

### Triangulation

```text
Test: total([5]) == 5
Run tests -> fails
Implement: return 5
Run tests -> passes

Test: total([5, 7]) == 12
Run tests -> fails
Implement: sum all item amounts
Run tests -> passes
Refactor -> improve naming if needed
```

### Refactor only on green

```text
Green: discount rule works for the covered examples
Refactor: extract duplicated rate calculation
Run tests -> still green
```

## References

- Kent Beck, *Test-Driven Development: By Example*. Addison-Wesley, 2002.
- Kent Beck, "Part I: The Money Example" preview, O'Reilly. https://www.oreilly.com/library/view/test-driven-development/0321146530/part01.xhtml
- Kent Beck, "Part III: Test-Driven Development Patterns" preview, O'Reilly. https://www.oreilly.com/library/view/test-driven-development/0321146530/part03.xhtml
