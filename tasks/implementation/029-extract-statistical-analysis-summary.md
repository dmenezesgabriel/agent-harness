---
id: "029"
issue: "tasks/issues/029-extract-statistical-analysis-module.md"
created: 2026-05-23
updated: 2026-05-23
---

# Implementation Summary: Extract statistical analysis module

## Related Task

- `tasks/issues/029-extract-statistical-analysis-module.md`

## Files Changed

- `benchmarks/harness/analysis.py` — new module: `TrialStats` dataclass and `analyze_trials()` pure function
- `benchmarks/harness/models.py` — added `trial_stats: dict[str, TrialStats]` field to `ExperimentSummary`
- `benchmarks/harness/runner.py` — removed `_statistical_test()`, replaced with `analyze_trials()` calls; removed `cohens_d` import; removed inline `scipy.stats` import
- `benchmarks/tests/test_analysis.py` — new test file: UT-001 through UT-006, IT-001, plus `TrialStats` field verification

## Behavior Implemented

- `harness/analysis.analyze_trials()` performs Wilcoxon signed-rank test (n >= 5) and Cohen's d effect size computation in isolation.
- `TrialStats` dataclass bundles `p_value`, `effect_size`, `test_name`, `significant`, and `note` into a single result.
- Runner delegates statistical computation to `analyze_trials()` for each tested metric and stores `TrialStats` in `ExperimentSummary.trial_stats`.
- Backward compatible: `p_values` and `effect_sizes` dicts remain populated (extracted from `TrialStats`).
- Edge cases: empty input raises `ValueError`; fewer than 5 pairs skips Wilcoxon (note explains); zero variance sets `effect_size=0.0` and explains in note.

## Design Notes

- `TrialStats` is defined in `analysis.py` alongside `analyze_trials()` — the return type lives with its producer.
- `models.py` imports `TrialStats` from `analysis.py` (no circular dependency).
- `analysis.py` has zero transitive dependencies on harness runner/adapters/evaluators/tracking — only `statistics`, `math`, `scipy.stats`, and `dataclasses` (matches `FR-007`).
- Used `statistics.pstdev` (population std) to match existing `cohens_d` computation behavior.
- Runner skips metrics with empty score lists (happens with `with_skill_only=True`) to avoid `ValueError` from `analyze_trials`.
- AC-001 example data uses 6 pairs to ensure `p < 0.05` is achievable with Wilcoxon signed-rank (minimum two-sided p for n=6 is 0.03125).

## Tests Added or Updated

- `tests/test_analysis.py:test_clear_signal_returns_significant` — UT-001: 6 pairs with clear gap → p < 0.05, significant=True
- `tests/test_analysis.py:test_fewer_than_five_pairs_returns_not_significant` — UT-002: 2 pairs → significant=False, non-empty note
- `tests/test_analysis.py:test_zero_variance_returns_effect_size_zero` — UT-003: identical scores → effect_size=0.0, non-empty note
- `tests/test_analysis.py:test_empty_with_scores_raises_value_error` — UT-004: empty with_scores → ValueError
- `tests/test_analysis.py:test_empty_without_scores_raises_value_error` — UT-005: empty without_scores → ValueError
- `tests/test_analysis.py:test_deterministic_identical_inputs` — UT-006: same inputs → identical outputs
- `tests/test_analysis.py:test_trial_stats_dataclass_fields` — validates `TrialStats` field access
- `tests/test_analysis.py:test_runner_summary_contains_trial_stats` — IT-001: BenchmarkRunner produces ExperimentSummary with non-None TrialStats per metric

## Test Categories Not Applicable

- `Smoke`: Not applicable — no startup or deploy boundary.
- `End-to-End`: Not applicable — no user-visible output change; `ExperimentSummary` values are identical.
- `Regression`: Not applicable — no known previous defect related to statistical computation.
- `Performance`: Not applicable — statistical computation at experiment scale (≤50 trial pairs) is fast.
- `Security`: Not applicable — no trust boundary, input-handling, or data-exposure changes.
- `Usability`: Not applicable — no user-facing behavior change.
- `Observability`: Not applicable — no log, metric, or trace changes.

## Validation Run

```text
pytest tests/ — 58 passed (50 existing + 8 new)
grep "scipy" harness/runner.py — no matches (AC-005)
grep "^import\|^from" harness/analysis.py — only stats/math/dataclasses/scipy (AC-006)
```

## Accessibility Notes

Not applicable — this task does not change frontend UI.

## Observability Changes

Not applicable — statistical analysis is a pure computation; no logging, metrics, or traces added.

## ADR Updates

Not applicable — extracting a computation into its own module is not an architecture-shaping decision.

## Unresolved Assumptions or Follow-Up

None.
