---
id: "2026-06-02-skill-evaluator-token-efficient-coverage"
issue: "inline request: improve skill-evaluator value proof while staying token efficient"
status: completed
completed: 2026-06-02
---

# Implementation: Token-efficient skill evaluator coverage

## Changes

### `skills/skill-evaluator/SKILL.md`

- Documented `trigger` and `compare` modes.
- Clarified when to use `invoke`, `compare`, `trigger`, and `all`.
- Documented `--input-fixture-limit` and the default two-fixture cap.

### `skills/skill-evaluator/evals/`

- Added trigger queries for evaluator activation checks.
- Added minimal deterministic report-shape fixtures and Behave steps.
- Added golden checks for skill name/mode, structural evidence, input size, and pass rate.

### `skills/skill-evaluator/runner/`

- Added `input_fixture_limit` CLI/model setting with default `2`.
- Updated skill and baseline invocation to run the first two sorted input fixtures by default.
- Namespaced multi-fixture artifacts by input fixture stem to avoid output collisions.
- Aligned skill input-size reporting with the invoked fixture subset.
- Allowed `skill-evaluator` self-evals when explicitly requested while keeping it excluded from default all-skill discovery.

## Acceptance Criteria Verification

| Item | Status | Evidence |
|------|--------|----------|
| Token-efficient fixture coverage | PASS | Default cap is 2; `--input-fixture-limit` can lower or raise it. |
| Avoid single-fixture blindness | PASS | `SkillInvoker` now invokes up to two sorted input fixtures for skill and baseline runs. |
| Do not overstate token cost | PASS | `SkillInputSizer` counts only invoked input fixtures. |
| Prove skill value over baseline | PASS | `compare` mode is documented and remains implemented in runner strategy. |
| Validate evaluator skill itself | PASS | `skill-evaluator/evals` includes trigger queries and deterministic report checks. |

## Validation

```
uv run python -m runner.run --skill skill-evaluator --mode invoke --input-fixture-limit 2
Structural: 2 passed, 0 failed

uv run ruff format --check runner tests
uv run ruff check runner tests
uv run ruff format --check ../../skill-evaluator/evals
uv run ruff check ../../skill-evaluator/evals
uv run pytest
118 passed in 0.40s
```

## Unresolved Assumptions or Follow-Up

- Mitigated in follow-up: multi-fixture generated artifacts now run structural checks per input fixture directory, with fixture-prefixed scenario names in reports.
