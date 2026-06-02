---
id: "003"
issue: fixture-scoped-judge-artifact-selection
created: 2026-06-02
updated: 2026-06-02
---

# Implementation Summary: Fixture-Scoped Judge Artifact Selection

## Related Task

Fix the regression where generated rubric judging selected artifacts relative to the multi-fixture _generated_artifacts root instead of each per-fixture artifact directory.

## Files Changed

- `skills/skill-evaluator/runner/runner/judging.py` — Runs generated rubrics once per fixture artifact directory, labels fixture-scoped rubric IDs, and pairs compare-mode judge calls by fixture name.
- `skills/skill-evaluator/runner/tests/test_judging.py` — Adds regression coverage for anchored path selectors inside per-fixture artifact dirs in judge and compare modes.


## Behavior Implemented

Generated rubric judging now mirrors structural fixture coverage: when _generated_artifacts contains input_* fixture directories, each generated rubric is evaluated against each fixture directory so anchored selectors such as tasks/issues/*.md match the artifact layout produced by multi-fixture invocation. Verdict rubric IDs are labeled with the fixture stem to keep report and compare rows distinct. Flat single-fixture artifact directories keep the existing one-rubric-one-verdict behavior.

## Design Notes

The selector itself remains unchanged. The fix changes the root passed into selection for generated artifacts, which preserves existing anchored rubric path patterns and avoids reintroducing global largest-artifact selection across fixtures. Compare mode pairs skill and baseline fixture directories by fixture name and emits missing-artifact verdicts instead of accidentally matching a different fixture when one side is absent.

## Tests Added or Updated

Added judge-mode and compare-mode regression tests that create input_* fixture subdirectories containing tasks/issues/*.md artifacts and assert that each fixture receives a distinct fixture-labeled verdict.

## Test Categories Not Applicable

- Accessibility testing is not applicable because no UI or user interaction behavior changed.
- End-to-end LLM provider testing was not run because the regression is covered with deterministic fake judges and filesystem fixtures.


## Validation Run

```text
uv run pytest tests/test_judging.py
uv run ruff check runner/judging.py tests/test_judging.py
uv run mypy
uv run pytest
```

## Accessibility Notes

No accessibility impact; this change only affects backend evaluator artifact selection and judge result labeling.

## Observability Changes

Existing judge_start, judge_done, compare_judge_start, and compare_judge_done logs now receive fixture-labeled rubric_id values for per-fixture generated artifact verdicts.

## ADR Updates

No ADR update was needed; this preserves the existing multi-fixture evaluation architecture and aligns judge behavior with the structural runner.

## Unresolved Assumptions or Follow-Up

Assumes fixture-labeled rubric IDs are acceptable in reports and compare output because duplicate raw rubric IDs would otherwise collapse baseline comparison maps. No follow-up is required.
