---
id: "002"
created: 2026-06-01
updated: 2026-06-01
status: active
---

# Task: Split generated vs golden checks in comparison report

## Priority

P1 — Depends on no prior task but delivers the second identified fix: the structural comparison section currently aggregates all scenarios (golden fixture + generated), making the delta unreadable because golden checks always score identically between skill and baseline.

## Dependencies

- No task dependency; this is a pure reporting change independent of Task 001.
- No ADR dependency; this task uses only the existing `ScenarioResult.feature` field and `MarkdownReportWriter`.

## Assignability

**AFK** — fully specified, safe to delegate to an autonomous agent without human review mid-task.

## Context

`BehaveStructuralRunner` runs two behave passes per evaluation: one tagged `golden` (against static fixture files in `fixtures/golden/`) and one tagged `generated` (against live artifacts from the invocation). `ScenarioResult.feature` already encodes which pass a scenario came from — golden feature names contain "golden fixture validation" and generated feature names contain "generated skill output validation".

In compare mode the `_comparison_lines` method in `MarkdownReportWriter` aggregates all active scenarios into a single table and computes one delta. Because golden fixture scenarios always run against the same static files, skill and baseline will always match on them. The delta is therefore diluted: if skill passes 12/16 and baseline passes 9/16, 13 of those 16 rows are guaranteed ties (golden). The meaningful signal lives in the ~3 generated rows, but they are buried.

The fix splits the comparison table into two subsections — **Generated (contrastive)** and **Golden (fixture)** — so the reader immediately sees where the skill actually helped, without arithmetic.

The change is confined to `_comparison_lines` (and its private helpers) in `runner/reporting.py`. No model changes, no strategy changes, no CLI changes.

Files to change:
- `runner/reporting.py` — split `_comparison_lines` into generated and golden subsections based on `ScenarioResult.feature`
- `tests/test_reporting.py` — cover the new split rendering

## Use Cases

- **Feature**: Comparison report readability
- **Scenario**: Evaluator reads compare report after running dataviz
- **Given** a compare run produced 13 golden scenarios (all ties) and 3 generated scenarios (skill passed 3, baseline passed 1)
- **When** the evaluator opens the markdown report
- **Then** the `## Baseline comparison` section shows two subsections: `### Generated (contrastive)` and `### Golden (fixture)`
- **And** the generated subsection delta reads `+2 checks` making the skill contribution immediately visible
- **And** the golden subsection total reads `0 delta` confirming those rows are uninformative by design

## Definition of Ready

- `ScenarioResult.feature` field exists and is populated with the behave feature name (confirmed: `_parse_behave_results` sets `feature=str(feature.get("name", "unknown"))`).
- Feature names for the two passes are stable: golden features contain `"golden"` and generated features contain `"generated"` (confirmed from `golden.feature` and `generated_chart.feature` files).
- `_comparison_lines` and `_comparison_rows` in `reporting.py` are the only methods that need changing.

## Functional Requirements

- `FR-001`: `_comparison_lines` must separate active scenarios into two groups based on whether `ScenarioResult.feature` contains `"generated"` (case-insensitive) — one group for contrastive/generated checks and one for fixture/golden checks.
- `FR-002`: The `## Baseline comparison` section must render a `### Generated (contrastive)` subsection for generated scenarios and a `### Golden (fixture)` subsection for golden scenarios.
- `FR-003`: Each subsection must show its own delta line: `Skill improvement: <delta> checks vs baseline (<skill_passes> skill / <baseline_passes> baseline)`.
- `FR-004`: If either group is empty, its subsection must be omitted — do not render an empty table.
- `FR-005`: The full overall delta line that currently exists at the bottom of `_comparison_lines` must be replaced by the two per-subsection delta lines; no duplicate aggregation.

## Non-Functional Requirements

- `NFR-001`: The split must not change any other report section — `## Structural checks`, `## LLM-as-judge checks`, `## Trigger routing checks`, `## Skill input size`, and `**Pass rate**` must render identically before and after this change.
- `NFR-002`: The change must pass `make check` with no new mypy, ruff, deptry, or vulture errors.

## Observability Requirements

Not applicable — this task changes only markdown rendering; no log, metric, or trace behavior is introduced or modified.

## Acceptance Criteria

- `AC-001`: **Given** `_comparison_lines` is called with scenarios where some have `feature` containing `"generated"` and some containing `"golden"`, **When** the output is rendered, **Then** it contains both `### Generated (contrastive)` and `### Golden (fixture)` headers.
- `AC-002`: **Given** 3 generated scenarios (skill: 3 passed, baseline: 1 passed) and 13 golden scenarios (skill: 13 passed, baseline: 13 passed), **When** the report is rendered, **Then** the generated subsection shows delta `+2` and the golden subsection shows delta `+0`.
- `AC-003`: **Given** no generated scenarios (all scenarios are golden), **When** the report is rendered, **Then** the `### Generated (contrastive)` subsection is absent — to avoid presenting an empty table where no contrastive signal exists.
- `AC-004`: **Given** no golden scenarios (all scenarios are generated), **When** the report is rendered, **Then** the `### Golden (fixture)` subsection is absent.
- `AC-005`: **Given** `baseline_results` is `None` or empty, **When** the report is rendered, **Then** the `## Baseline comparison` section is omitted entirely — same guard behavior as before this task.

## Required Tests

### Unit Tests

- `UT-001`: `_comparison_lines` with mixed generated and golden scenarios renders both subsection headers. Covers `FR-002`, `AC-001`.
- `UT-002`: Generated subsection delta is computed only from generated scenarios; golden subsection delta only from golden scenarios. Covers `FR-003`, `AC-002`.
- `UT-003`: `_comparison_lines` omits `### Generated (contrastive)` when no scenarios have a "generated" feature name. Covers `FR-004`, `AC-003`.
- `UT-004`: `_comparison_lines` omits `### Golden (fixture)` when no scenarios have a "golden" feature name. Covers `FR-004`, `AC-004`.
- `UT-005`: `_comparison_lines` returns empty list when `baseline_results` is `None` — no regression on existing guard. Covers `AC-005`.
- `UT-006`: All non-comparison report sections (`## Structural checks`, `**Pass rate**`, `## LLM-as-judge checks`) are unaffected by the split. Covers `NFR-001`.

### Integration Tests

Not applicable — the change is a pure string-rendering function; no real boundary is crossed.

### Smoke Tests

Not applicable — no deploy, startup, or critical-path availability changed.

### End-to-End Tests

Not applicable — no complete user journey changed; the report file gains subsection headers but the CLI interface is unchanged.

### Regression Tests

Not applicable — no previously broken defect being fixed.

### Performance Tests

Not applicable — string rendering; no measurable performance risk.

### Security Tests

Not applicable — no authentication, authorization, input handling, storage, secrets, or external communication touched.

### Usability Tests

Not applicable — output is a markdown file; no interactive UI changed.

### Observability Tests

Not applicable — this task introduces no logs, metrics, traces, or analytics events.

## Definition of Done

- `_comparison_lines` in `reporting.py` splits scenarios by `ScenarioResult.feature` into generated and golden subsections.
- Each subsection shows its own delta line; the single aggregated delta line is removed.
- Empty subsections are omitted.
- All required unit tests pass under `make check`.
- `make check` passes with no new mypy, ruff, deptry, or vulture errors.
