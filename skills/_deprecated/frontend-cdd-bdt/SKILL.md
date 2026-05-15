---
name: frontend-cdd-bdt
description: Use Component-Driven Development and Behavior-Driven Testing to implement frontend features safely, accessible behavior, explicit UI states, component contracts, composition boundaries, visual consistency, and critical user flows.
---

## Purpose

Use Component-Driven Development as the frontend implementation workflow and Behavior-Driven Testing as the behavioral safety net.

Apply to new features, UI refactors, design-system work, interaction fixes, accessibility remediation, and regression prevention.

This skill is framework-agnostic.

## Core Loop

1. Behavior: define user-visible behavior, acceptance criteria, and interaction states.
2. Component: build the smallest isolated component or composition boundary.
3. Test: verify observable behavior, accessibility, state transitions, and contracts.
4. Compose: integrate into the screen, route, form, or flow.
5. Validate: protect critical journeys with integration, E2E, visual, and accessibility checks.

Prefer isolated, accessible, behavior-preserving increments over broad UI rewrites.

Key terms: Component-Driven Development, Behavior-Driven Testing, Given-When-Then, acceptance criteria, component contract, accessible interaction, UI state model, composition boundary.

## When to Use

Use when frontend work involves:

- New UI features or interaction flows
- Complex component state
- Forms, validation, or submission behavior
- Conditional rendering
- Design-system components
- Accessibility issues
- Visual regressions
- Routing, auth, or navigation flows
- API-connected UI states
- Reusable component extraction
- Over-coupled components
- Props/state confusion
- UI logic mixed with infrastructure
- Brittle implementation-coupled tests

## Principles

### Start from User Behavior

Define behavior before implementation using user stories, acceptance criteria, or Given-When-Then scenarios.

Focus on what the user can perceive, trigger, and verify.

Key terms: BDD, scenario, acceptance criteria, user-visible behavior.

### Model States Explicitly

Identify relevant states before coding: idle, loading, success, empty, error, disabled, selected, expanded, focused, and invalid.

Avoid implicit state scattered across unrelated booleans.

Key terms: UI state model, state transition, finite state, empty state, error state.

### Build Components in Isolation

Implement isolated components with realistic props, fixtures, mock data, and interaction examples before composing screens.

Key terms: CDD, isolated component, story, fixture, playground, design-system primitive.

### Test Behavior, Not Implementation

Assert semantic output and user interactions, not private state, internal functions, CSS classes, or component hierarchy.

Prefer queries by role, label, text, and accessible name.

Key terms: black-box test, Testing Library principle, accessible query, semantic assertion, implementation detail.

### Treat Accessibility as Contract

Accessibility is part of the component contract, not final polish.

Verify semantic HTML, accessible names, labels, roles, keyboard support, focus management, disabled states, error messages, and ARIA only when needed.

Key terms: WCAG, accessible name, keyboard navigation, focus management, semantic HTML, ARIA.

### Separate UI Policy from Effects

Keep formatting, validation, state transitions, and decision logic separate from API calls, browser APIs, timers, storage, and other side effects.

Place effects at boundaries.

Key terms: functional core / imperative shell, pure UI logic, side-effect boundary, adapter.

### Keep Components Cohesive

A component should own one clear responsibility: primitive, stateful interaction, layout composition, feature container, or screen.

Avoid mixing fetching, domain policy, layout, formatting, and low-level interaction behavior in one component.

Key terms: cohesion, responsibility boundary, container/presentational split, feature boundary.

### Compose Instead of Over-Configuring

Prefer children, slots, and composition over large prop APIs, boolean explosions, prop drilling, and variant matrices.

Extract only when reuse, ownership, or variation is real.

Key terms: composition over configuration, slot, children, variant axis, boolean trap, prop drilling.

### Mock at Boundaries

Mock network, time, storage, permissions, browser APIs, and nondeterministic dependencies.

Do not mock the component under test or mirror internal implementation.

Key terms: MSW, fake, stub, test double, boundary mock, contract test.

### Validate Critical Flows Selectively

Use integration tests for connected behavior, E2E tests for high-value journeys, and visual regression for stable high-value UI.

Do not snapshot every detail or cover every component path with E2E.

Key terms: critical path, user journey, regression path, Playwright, Cypress, visual regression, screenshot test.

## Remediation Rules

Be specific. Do not only say:

- Add frontend tests
- Use Storybook
- Improve accessibility
- Refactor component
- Add E2E tests
- Make it reusable

Instead state:

- Which user behavior must be protected
- Which UI state is missing or ambiguous
- Which component contract is unclear
- Which interaction needs a behavior test
- Which accessibility requirement belongs to the contract
- Which side effect belongs behind a boundary
- Which responsibility should be split
- Which props create over-configuration
- Which flow deserves E2E protection
- Which abstraction would be premature

## Output Format

For each item, use:

### Implementation: precise frontend concern

Priority: High | Medium | Low

User behavior:
Observable behavior, interaction, state transition, or acceptance scenario.

Component boundary:
Primitive, composed component, feature component, or screen responsibility.

First test:
Behavior, accessibility, interaction, integration, visual, or E2E test.

Smallest change:
Minimum implementation change to satisfy the behavior.

Composition step:
How it integrates into the screen, route, form, or flow.

Accessibility contract:
Required role, label, keyboard behavior, focus behavior, or error announcement.

Target shape:
Intended state model, component contract, composition boundary, data boundary, or test boundary.

Risk:
Brittle selectors, over-mocking, prop explosion, inaccessible interaction, visual fragility, or premature abstraction.

## Sequence

1. Define user behavior and acceptance criteria.
2. List required UI states and transitions.
3. Create isolated component examples with realistic fixtures.
4. Write the first failing behavior or accessibility test.
5. Implement the smallest accessible behavior.
6. Add loading, empty, error, disabled, and invalid states explicitly.
7. Separate pure UI logic from side effects.
8. Mock external boundaries, not internal components.
9. Compose into the feature, screen, route, or form.
10. Add integration tests for connected behavior.
11. Add E2E tests only for critical journeys.
12. Add visual regression only for stable high-value UI.
13. Refactor props, names, and boundaries while behavior stays protected.
14. Keep the component tree shallow and cohesive.

## Core Principle

Frontend implementation should be driven by user-visible behavior, explicit UI states, accessible component contracts, and stable composition boundaries.

Use CDD to build isolated, cohesive UI parts.

Use BDT to protect interactions, accessibility, integration behavior, and critical user journeys.

Introduce abstractions, variants, slots, and test seams only when they reduce coupling, clarify ownership, protect behavior, or make change safer.
