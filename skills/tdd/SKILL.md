---
name: tdd
description: Use when the user asks to work test-first — write a failing test before the code, drive a change or bug fix red-green-refactor, or pin a bug with a regression test. Not for questions that define or explain TDD, red-green-refactor, or testing terms.
---

# Test-driven development

TDD is the red → green → refactor loop: one failing test, the smallest change that passes it, then clean up. The test drives the design — each cycle teaches the next what the interface wants.

**The loop:**
1. **Red:** write the smallest test that encodes the intended behavior. Run it and watch it fail for the reason you expect; a test that fails for the wrong reason needs fixing before the code does.
2. **Green:** make the smallest change that passes it. Nothing more — speculation belongs to no cycle.
3. **Refactor:** clean the design while green. Restructuring inside red is how both break.

**Rules:**
- One behavior per cycle — vertical slices, never all tests then all code.
- Expected values come from the spec, not from a run of the code under test (see [principle-test-behavior-not-implementation](../principle-test-behavior-not-implementation/SKILL.md)).
- If a failing test is impractical — broad harness, mocks that would test themselves — use the closest executable check and say so. Prefer no new test over a bad one.

**Gotchas:**
- Do not change a test to match wrong code; the red must mean the behavior is wrong.
- A test that cannot fail proves nothing.
- The regression test stays: it encodes the bug so the bug cannot return quietly.

Source: Kent Beck, *Test Driven Development: By Example*; red–green–refactor.
