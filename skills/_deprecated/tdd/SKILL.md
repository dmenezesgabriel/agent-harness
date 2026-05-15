---
name: tdd
description: Use TDD to implement features and remediate design issues safely, low cohesion, tight coupling, weak encapsulation, poor boundaries, infrastructure leakage, brittle tests, and over-fragmentation.
---

## Purpose

Use Test-Driven Development as a design feedback loop: protect behavior, make the smallest change, then refactor toward clearer boundaries.

Apply to new features, bug fixes, and design remediation.

This skill is language-agnostic.

## Core Loop

1. Red: write a failing test for required behavior, regression risk, invariant, or missing seam.
2. Green: make the smallest change that passes.
3. Refactor: improve design while tests stay green.

Prefer incremental, behavior-preserving change over broad rewrites.

Key terms: Red-Green-Refactor, characterization test, regression test, observable behavior, behavior-preserving refactor, test seam, contract test.

## When to Use

Use when code shows:

- Low cohesion or multiple reasons to change
- Tight coupling or wrong dependency direction
- Mixed abstraction levels
- Hidden side effects
- Duplicated domain policy
- Poor testability
- Infrastructure leakage
- Weak encapsulation or unprotected invariants
- Unclear ownership or boundaries
- Recurring variation axes
- Over-fragmentation or premature abstraction
- Brittle workarounds

## Principles

### Characterize Before Changing

For risky existing code, add characterization tests around current observable behavior before refactoring.

Avoid asserting private methods, internal call order, or file structure unless no stable public contract exists.

Key terms: characterization test, approval test, golden master, regression safety net.

### Test Behavior, Not Structure

Tests should describe domain rules, public contracts, invariants, and observable outcomes.

Avoid brittle tests coupled to implementation details.

Key terms: black-box test, public contract, invariant, implementation detail.

### Separate Decisions from Effects

When logic is mixed with I/O, first protect behavior, then extract deterministic decision logic into a pure core.

Keep side effects in a thin imperative shell.

Key terms: functional core / imperative shell, pure function, side-effect boundary.

### Create Seams Only When Useful

Introduce seams only to isolate volatile, slow, nondeterministic, or external dependencies.

Valid seams: dependency injection, function parameters, ports, adapters, fakes, stubs, contract tests.

Avoid seams that only mirror the current implementation.

Key terms: test seam, dependency injection, port, adapter, fake, stub, mock.

### Correct Dependency Direction

Core policy must not depend on infrastructure.

Test core behavior without real infrastructure, introduce a port, and move concrete details behind an adapter.

Key terms: Dependency Inversion Principle, Dependency Rule, policy/detail separation, port, adapter.

### Protect Invariants at the Owner

Enforce invariants inside the owning domain object, value object, aggregate, or domain service.

Do not rely only on controllers, UI components, database constraints, or scattered callers.

Key terms: encapsulation, invariant protection, value object, domain service, Tell Don’t Ask.

### Let Tests Reveal Boundaries

Extract a responsibility only when tests expose a distinct behavior, invariant, side effect, ownership rule, or variation axis.

Do not split code just to create smaller files.

Key terms: Single Responsibility Principle, cohesion, divergent change, responsibility boundary.

### Add Extension Points Late

When repeated conditionals represent real variation, test each variant first.

Then introduce a strategy, rule object, registry, polymorphism, or adapter only if it reduces coupling or isolates change.

Key terms: Open/Closed Principle, Protected Variation, strategy, polymorphism, variation axis.

### Avoid Over-Fragmentation

Prefer shallow, cohesive, locally understandable structures.

A new abstraction is justified only when it reduces coupling, protects invariants, isolates volatility, improves testability, clarifies ownership, or enforces a boundary.

Key terms: Simple Design, locality of behavior, locality of change, indirection cost, premature abstraction, speculative generality.

## Remediation Rules

Be specific. Do not only say:

- Add tests
- Use TDD
- Refactor with tests
- Mock dependencies
- Improve testability

State exactly:

- Which behavior must be characterized first
- Which invariant or contract needs protection
- Which dependency blocks isolated testing
- Which side effect belongs behind a boundary
- Which responsibility can be extracted safely
- Which seam, port, or adapter is justified
- Which abstraction would be premature
- Which smallest behavior-preserving step comes next

## Output Format

For each item, use:

### Remediation: precise design issue

Priority: High | Medium | Low

Design issue:
Name the structural problem.

Behavior to protect:
Observable behavior, rule, invariant, or contract that must remain true.

First test:
First failing test, characterization test, or regression test.

Smallest change:
Minimum implementation change to pass.

Refactor step:
Behavior-preserving design improvement.

Target shape:
Intended responsibility split, dependency direction, seam, port, adapter, or boundary.

Risk:
Brittle tests, excessive mocking, over-abstraction, or over-fragmentation risk.

## Sequence

1. Characterize current behavior.
2. Add regression tests for known bugs.
3. Write one failing test for the desired behavior or seam.
4. Make the smallest passing change.
5. Extract pure logic from side effects.
6. Move domain policy out of delivery/infrastructure code.
7. Protect invariants in the owning domain model.
8. Introduce ports only for external dependencies or real variation axes.
9. Move infrastructure behind adapters.
10. Add contract tests for adapters.
11. Replace duplicated conditionals only when tests prove recurring variation.
12. Refactor names and boundaries while tests stay green.
13. Keep the structure shallow.

## Core Principle

TDD should drive safer behavior and better boundaries, not more ceremony.

Introduce seams, abstractions, ports, adapters, and patterns only when they improve isolation, protect behavior, reduce coupling, clarify ownership, or make change safer.
