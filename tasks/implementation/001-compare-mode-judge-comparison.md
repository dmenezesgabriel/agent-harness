---
id: "001"
task: tasks/issues/001-compare-mode-judge-comparison.md
status: completed
completed: 2026-06-01
---

# Implementation: Add judge comparison to compare mode

## Changes

| File | Change |
|------|--------|
| `runner/runner/models.py` | Added `baseline_judge_verdicts: list[JudgeReport]` field to `EvalOutcome` |
| `runner/runner/strategies/compare.py` | Added `judge_runner: RubricJudgeRunner` and `judge: JudgePort` as required constructor params; call judge on both artifact dirs in `run()` |
| `runner/runner/run.py` | Injected `RubricJudgeRunner()` and `cast(JudgePort, adapter)` into `CompareStrategy` for `Mode.COMPARE` |
| `runner/runner/reporting.py` | Added `baseline_judge_verdicts` param to `write()` and `_report_lines()`; added `_judge_comparison_lines()` static method |
| `runner/runner/ports.py` | Added `baseline_judge_verdicts` to `ReportWriterPort.write()` signature |
| `runner/runner/evaluation.py` | Pass `outcome.baseline_judge_verdicts or None` to report writer |
| `runner/tests/strategies/test_compare.py` | Added `FakeJudgeRunner`, `FakeJudge`, `_make_strategy` helper; updated existing tests; added `TestCompareStrategyJudge` with UT-001, UT-002, UT-005, OT-001 |
| `runner/tests/test_reporting.py` | Added `TestMarkdownReportWriterJudgeComparison` with UT-003, UT-004 |
| `runner/tests/test_evaluation.py` | Updated `FakeReportWriter.write()` to accept `baseline_judge_verdicts` kwarg |

## Criteria verified

- AC-001 ✅ — `outcome.judge_verdicts` = skill verdicts, `outcome.baseline_judge_verdicts` = baseline verdicts
- AC-002 ✅ — `## Judge comparison` table rendered with per-rubric rows
- AC-003 ✅ — Section omitted when no rubrics
- AC-004 ✅ — `run.py` wires `RubricJudgeRunner` and `JudgePort` into `CompareStrategy`; mypy passes
- AC-005 ✅ — Delta `+0.30` for skill=0.9, baseline=0.6
- FR-001..FR-007 ✅ — All functional requirements met
- NFR-001 ✅ — Table format matches `## LLM-as-judge checks`
- NFR-002 ✅ — `make check` passes (94 tests, mypy clean, all linters pass)
- OBS-001 ✅ — `RubricJudgeRunner` unchanged; emits `judge_start`/`judge_done` for both passes

## Test results

```
94 passed in 1.52s — coverage 88.21%
```
