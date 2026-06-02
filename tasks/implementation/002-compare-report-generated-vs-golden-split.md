---
id: "002"
issue: "tasks/issues/002-compare-report-generated-vs-golden-split.md"
status: completed
completed: 2026-06-02
---

# Implementation: Split generated vs golden checks in comparison report

## Changes

### `skills/skill-evaluator/runner/runner/reporting.py`

- **Replaced** `_comparison_lines` to split `structural_results` into two groups:
  - `generated`: scenarios where `feature.lower()` contains `"generated"`
  - `golden`: all other scenarios
- **Added** `_comparison_subsection_lines(header, scenarios, baseline_by_scenario)` — renders one subsection table plus its own delta line. Reuses `_comparison_rows`.
- The old single aggregated delta line is gone; each subsection carries its own `**Skill improvement**: …`.
- Empty subsections are omitted (`if generated: …`).

### `skills/skill-evaluator/runner/tests/test_reporting.py`

Added `TestMarkdownReportWriterComparisonSplit` with 6 tests:

| Test | Covers |
|------|--------|
| `test_renders_both_subsection_headers_with_mixed_scenarios` | UT-001 / AC-001 |
| `test_subsection_deltas_computed_independently` | UT-002 / AC-002 |
| `test_omits_generated_subsection_when_no_generated_scenarios` | UT-003 / AC-003 |
| `test_omits_golden_subsection_when_no_golden_scenarios` | UT-004 / AC-004 |
| `test_omits_baseline_section_when_baseline_results_none` | UT-005 / AC-005 |
| `test_non_comparison_sections_unaffected_by_split` | UT-006 / NFR-001 |

## Acceptance Criteria Verification

| Item | Status | Evidence |
|------|--------|----------|
| AC-001 | PASS | `### Generated (contrastive)` and `### Golden (fixture)` both rendered when mixed input |
| AC-002 | PASS | UT-002 asserts `+2` (generated) and `+0` (golden) appear in report |
| AC-003 | PASS | UT-003 asserts generated header absent when all scenarios are golden |
| AC-004 | PASS | UT-004 asserts golden header absent when all scenarios are generated |
| AC-005 | PASS | Guard `if not baseline_results: return []` unchanged; UT-005 confirms |
| FR-001 | PASS | Split condition: `"generated" in r.feature.lower()` |
| FR-002 | PASS | Two subsection headers rendered |
| FR-003 | PASS | `_comparison_subsection_lines` renders per-subsection delta line |
| FR-004 | PASS | `if generated:` / `if golden:` guards omit empty subsections |
| FR-005 | PASS | No top-level aggregated delta line remains |
| NFR-001 | PASS | UT-006 confirms structural, judge, and pass-rate sections unchanged |
| NFR-002 | PASS | `make check` passes: 100 tests, mypy clean, ruff clean, vulture/deptry/bandit/semgrep clean |

## Validation

```
make check: 100 passed in 1.53s — coverage 88.34% (threshold 75%)
```
