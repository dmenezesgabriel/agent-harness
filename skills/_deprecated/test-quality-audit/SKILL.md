---
name: test-quality-audit
description: Audit tests for meaningful coverage, behavior protection, reliability, maintainability, and change safety. Use for unit, integration, contract, behavioral, accessibility, visual, end-to-end, regression, mutation, load, and smoke tests.
---

## Purpose

Audit test suites for concrete quality issues that reduce confidence, correctness, reliability, maintainability, or change safety.

Tests must prove important application behavior, not exist only to increase coverage or satisfy the test runner.

This playbook is language-agnostic.

## When to Use

Use when reviewing:
- existing test suites
- new feature tests
- bug-fix regression tests
- TDD output
- frontend behavior tests
- integration and contract tests
- end-to-end tests
- CI quality gates
- flaky tests
- low-value coverage
- brittle mocks
- untested failure paths
- untested edge cases
- missing critical journey coverage
- mutation testing survivors
- tests that pass but do not prove correctness

Do not audit unrelated tests unless the requested change depends on them.

## Core Principle

A test should exist because it protects a meaningful behavior, rule, invariant, contract, integration point, user journey, failure mode, accessibility requirement, or operational risk.

A test that only asserts implementation details, repeats the implementation, or improves coverage without increasing confidence is test debt.

## Review Principles

### Behavior Value

Check whether each test protects observable behavior, domain rules, public contracts, user-visible outcomes, invariants, or integration behavior.

Flag tests that assert private methods, internal call order, incidental structure, framework mechanics, CSS classes, snapshots without intent, or implementation details.

Key terms: observable behavior, public contract, black-box test, invariant, semantic assertion, implementation detail, confidence.

### Coverage Quality

Check whether coverage includes meaningful cases, not only executed lines.

Required coverage should include:
- success path
- failure path
- edge cases
- boundary values
- invalid input
- empty input
- null/undefined/missing values where relevant
- permission/auth states
- timeout/retry/cancellation behavior where relevant
- concurrency/idempotency where relevant
- persistence and transaction behavior where relevant
- accessibility states where relevant
- regression cases for known bugs

Flag line coverage without assertion strength.

Key terms: branch coverage, path coverage, condition coverage, boundary value analysis, equivalence partitioning, edge case, assertion strength.

### Test Level Fit

Check whether the behavior is tested at the cheapest reliable level.

Use:
- Unit tests for pure logic, domain rules, invariants, algorithms, formatting, validation, and state transitions.
- Characterization tests for risky legacy behavior before refactoring.
- Regression tests for known bugs.
- Contract tests for ports, adapters, APIs, provider integrations, schemas, and message boundaries.
- Integration tests for connected modules, persistence, routing, SSR/server behavior, queues, jobs, and external adapter wiring.
- Behavioral/component tests for UI states, interactions, forms, accessibility, and component contracts.
- E2E tests for critical user journeys only.
- Accessibility tests for keyboard behavior, focus, semantic markup, labels, roles, and errors.
- Visual regression tests for stable high-value UI only.
- Mutation tests for important pure logic and domain rules where assertion strength matters.
- Load/performance tests for throughput, latency, concurrency, queues, jobs, and resource-sensitive paths.
- Smoke tests for startup, deployment, routing, configuration, container, serverless, and health checks.

Flag tests that are too high-level, too low-level, too broad, too slow, too brittle, or testing the wrong risk.

Key terms: test pyramid, test trophy, testing quadrants, contract test, integration boundary, critical path, risk-based testing.

### Assertion Quality

Check whether assertions would fail for the right reason when behavior breaks.

Flag weak assertions, no assertions, snapshot-only assertions, excessive golden files, broad truthiness checks, duplicated implementation logic, and tests that only verify mocks were called.

Assertions should verify outcomes, state changes, emitted events, persisted data, returned values, visible UI, accessible output, or boundary contracts.

Key terms: assertion strength, oracle, false positive, false negative, semantic assertion, outcome assertion.

### Failure and Recovery

Check whether failure behavior is tested explicitly.

Required failure coverage may include:
- validation errors
- authorization failures
- not found states
- conflicts
- duplicate operations
- network failures
- database failures
- timeout
- retry exhaustion
- partial failure
- rollback
- cancellation
- malformed external responses
- unavailable dependencies
- user correction after error

Flag tests that only cover happy paths when failures are likely or costly.

Key terms: negative test, error path, recovery path, rollback, idempotency, resilience.

### Test Data Quality

Check whether test data expresses intent clearly.

Flag random fixtures, oversized fixtures, copy-pasted setup, unclear magic values, production-shaped data with irrelevant fields, and tests where expected behavior is hidden inside setup noise.

Prefer minimal, named, intention-revealing data builders, factories, fixtures, examples, and Given-When-Then structure.

Key terms: test fixture, test data builder, factory, example, Given-When-Then, arrange-act-assert.

### Isolation and Boundaries

Check whether tests isolate the right thing and mock only real boundaries.

Mock external dependencies, nondeterminism, time, randomness, network, filesystem, browser APIs, queues, SDKs, permissions, and third-party services.

Do not mock the unit under test, domain logic under review, or internal collaborators just to match implementation.

Flag excessive mocking, brittle interaction tests, fake architecture created only for tests, and mocks that hide real contract failures.

Key terms: test double, fake, stub, mock, spy, boundary mock, contract test, test seam.

### Reliability and Determinism

Check whether tests are deterministic, parallel-safe, and stable in CI.

Flag flaky timing assumptions, sleeps, shared mutable state, order dependence, real network calls, timezone dependence, locale dependence, uncontrolled randomness, leaked state, race conditions, and environment-specific assumptions.

Key terms: deterministic test, flaky test, hermetic test, test isolation, race condition, clock control, seed control.

### Maintainability

Check whether tests are easy to read, modify, and trust.

Flag duplicated setup, unclear names, over-abstracted helpers, test logic more complex than production logic, hidden assertions, shared fixtures with invisible coupling, and tests that fail far from the cause.

Tests should act as executable documentation of behavior.

Key terms: readability, intention-revealing name, local setup, low cognitive load, executable specification, test debt.

### Regression Protection

Check whether previous bugs have direct regression tests.

A regression test should fail on the old bug and pass after the fix.

Flag bug fixes without regression tests, regression tests that do not reproduce the bug, and broad tests that would not catch the exact failure.

Key terms: regression test, bug reproduction, minimal failing case, defect prevention.

### Contract and Integration Confidence

Check whether boundaries are protected by contracts instead of duplicated assumptions.

Check schemas, DTOs, request/response shapes, events, commands, messages, database mappings, adapter behavior, provider assumptions, and compatibility rules.

Flag integration tests that mock the very boundary they claim to validate.

Key terms: contract test, schema validation, adapter contract, consumer-driven contract, compatibility.

### Frontend Test Quality

Check whether frontend tests verify user-visible behavior and accessibility.

Prefer queries by role, label, text, and accessible name.

Check:
- loading, success, empty, error, disabled, invalid, selected, expanded, focused states
- keyboard behavior
- focus management
- accessible names
- form validation
- error announcements
- API-connected state transitions
- routing and navigation behavior
- critical user flows

Flag tests coupled to component hierarchy, CSS classes, internal state, implementation-only hooks, and overuse of snapshots.

Key terms: accessible query, semantic assertion, UI state model, component contract, user-visible behavior.

### E2E Test Quality

Check whether E2E tests protect high-value journeys rather than duplicating lower-level coverage.

Good E2E tests cover:
- critical business flow
- auth/session flow
- payment or checkout flow
- onboarding flow
- data creation/edit/delete flow
- cross-page workflow
- production-like integration risk

Flag excessive E2E tests for small logic branches, brittle selectors, test order dependence, unrealistic data setup, and broad flows with unclear failure cause.

Key terms: critical journey, user journey, smoke path, stable selector, production-like flow.

### Mutation and Test Strength

Check whether important logic has tests strong enough to fail when behavior changes incorrectly.

Use mutation testing selectively for core logic, domain rules, calculations, validation, authorization, pricing, eligibility, state machines, and high-risk branching.

Flag survived mutants in important behavior, but do not require mutation testing for trivial glue code.

Key terms: mutation testing, survived mutant, killed mutant, assertion strength, behavioral sensitivity.

### Cognitive Debt in Tests

Flag test cognitive debt when maintainers must understand excessive setup, mocks, helpers, fixtures, global state, or implementation details before understanding what behavior is protected.

Reduce cognitive debt by using local setup, named examples, intention-revealing helpers, explicit assertions, and clear Given-When-Then structure.

Do not hide important behavior behind clever test abstractions.

Key terms: cognitive debt, test readability, fixture mystery, hidden assertion, setup noise.

## Test Quality Smells

Flag:
- tests without meaningful assertions
- tests that only assert mocks were called
- tests that mirror implementation logic
- tests coupled to private methods
- tests coupled to file structure or component hierarchy
- snapshot tests without explicit intent
- broad integration tests for simple pure logic
- unit tests that mock everything
- E2E tests for every branch
- only happy-path tests
- missing failure and recovery tests
- missing edge and boundary tests
- missing regression tests for fixed bugs
- brittle selectors
- sleeps and timing assumptions
- real network calls in normal CI tests
- shared mutable fixtures
- order-dependent tests
- excessive test helper abstraction
- unclear test names
- magic test data
- duplicated setup noise
- coverage thresholds hiding weak assertions
- tests disabled, skipped, quarantined, or ignored without owner and reason
- flaky tests treated as normal

## Review Rules

Be concrete, falsifiable, and test-specific.

Do not say:
- Add more tests
- Improve coverage
- Tests are weak
- Use better mocks
- Add E2E tests
- Add integration tests
- Make tests cleaner
- Test edge cases

Instead state:
- Which behavior is unprotected
- Which assertion is weak or irrelevant
- Which failure mode is missing
- Which edge case matters
- Which test level is wrong
- Which mock hides real risk
- Which fixture creates cognitive debt
- Which test is brittle and why
- Which regression test should exist
- Which smallest test change increases confidence

Do not require 100% coverage.

Do not treat line coverage as proof of quality.

Do not add tests for trivial implementation details unless they protect meaningful behavior.

Do not duplicate the same behavior at every test level unless the risk justifies it.

## Output Format

For each finding, use:

### Finding: precise test quality issue

Priority: High | Medium | Low

Category: Behavior Value | Coverage Quality | Test Level Fit | Assertion Quality | Failure Path | Edge Case | Test Data | Isolation | Reliability | Maintainability | Regression | Contract | Frontend Behavior | E2E | Mutation | Cognitive Debt

Issue:
Exact testing problem.

Evidence:
Specific test file, test case, assertion, fixture, mock, helper, skipped test, uncovered behavior, or missing scenario.

Risk:
What bug, regression, false confidence, flaky failure, maintenance burden, or production failure could escape.

Recommendation:
Smallest practical test improvement.

Target shape:
Expected test level, behavior, scenario, assertion, fixture, boundary, or validation strategy.

Example test intent:
A short natural-language description of the test that should exist.

## Audit Sequence

1. Identify the application behaviors, user journeys, domain rules, invariants, and external contracts that matter.
2. Map existing tests to those risks.
3. Check whether happy paths, failure paths, edge cases, and regressions are covered.
4. Verify that each test has meaningful assertions.
5. Verify that each behavior is tested at the cheapest reliable level.
6. Inspect mocks and fakes for boundary correctness.
7. Inspect fixtures for clarity and minimality.
8. Check frontend tests for accessibility and user-visible behavior.
9. Check integration and contract tests for real boundary confidence.
10. Check E2E tests for critical journey value and brittleness.
11. Check determinism, isolation, parallel safety, and CI reliability.
12. Identify test debt and cognitive debt.
13. Recommend the smallest set of tests that materially increases confidence.

## Coverage Heuristic

For each important behavior, ask:

- What proves the success path works?
- What proves expected failures are handled?
- What proves edge and boundary cases are safe?
- What proves invalid input is rejected?
- What proves side effects happen correctly?
- What proves side effects do not happen when they should not?
- What proves external contracts are respected?
- What proves the user sees the correct state?
- What proves previous bugs cannot return?
- What proves the test would fail if the behavior broke?

If none of these answers are clear, the coverage is probably weak.

## Priority Rules

High:
A critical behavior, domain rule, security rule, data integrity rule, payment/revenue path, accessibility blocker, or production integration can break without a failing test.

Medium:
Important behavior has partial coverage, weak assertions, missing failure paths, brittle mocks, or unclear test level.

Low:
The test suite works but has readability, duplication, fixture clarity, or maintainability issues that slow future change.

## Core Principle

Good tests are executable specifications of important behavior.

They should increase confidence, catch real regressions, support refactoring, document expected behavior, and reduce cognitive debt.

A test is valuable only if it would fail for a meaningful breakage and help a maintainer understand what behavior must remain true.