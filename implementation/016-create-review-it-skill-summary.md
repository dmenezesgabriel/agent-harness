---
id: "016"
issue: "issues/016-create-review-it-skill.md"
created: 2026-05-17
updated: 2026-05-17
---

# Implementation Summary: Create review-it skill

## Related Task

- `issues/016-create-review-it-skill.md`

## Files Changed

- `skills/review-it/SKILL.md` — main skill definition: frontmatter, when-not-to-use, 14-step core workflow, output requirement, before-marking-complete checklist, anti-patterns, final response
- `skills/review-it/assets/review-report-template.md` — output template covering overall verdict, findings table, AC evaluation, test coverage, observability, ADR compliance, convention notes, and unresolved follow-up
- `skills/review-it/references/review-rules.md` — core review behavioral rules: issue identification, code inspection, finding classification (Blocking/Non-blocking/Suggestion), AC/test/observability/ADR/convention evaluation, finding ID convention, verdict logic
- `skills/review-it/references/output-rules.md` — output directory rule, file naming convention, report content requirements, final response format
- `skills/review-it/scripts/ensure-reviews-dir.sh` — shell helper to create `reviews/` before writing reports
- `reviews/016-create-review-it-skill-review.md` — SMK-001 smoke test: review report for this task itself
- `implementation/016-create-review-it-skill-summary.md` — this file

## Behavior Implemented

- `review-it` can be invoked with an issue file argument or discovers the relevant issue from `issues/`.
- Reads the task contract (FRs, NFRs, ACs, OBS, Required Tests, ADR dependencies) from the issue file.
- Inspects actual code changes via `git diff` rather than relying on the implementation summary alone.
- Classifies each finding as Blocking, Non-blocking, or Suggestion with a specific requirement ID reference.
- Emits an unambiguous overall verdict: Pass (zero Blocking) or Fail (one or more Blocking).
- Writes a structured review report to `reviews/NNN-slug-review.md` using the template.
- Stops and prompts the user when no issue file can be identified (AC-008).
- Does not modify source files (NFR-004).

## Design Notes

- Follows the exact directory structure of plan-it and implement-it: `SKILL.md`, `assets/`, `references/`, `scripts/`.
- Three-level finding classification (Blocking/Non-blocking/Suggestion) was chosen to match the task's own NFR-002 definition; no additional levels were introduced.
- `review-rules.md` keeps all behavioral logic; `SKILL.md` references it by section anchor — same pattern used by plan-it referencing `planning-rules.md`.
- `ensure-reviews-dir.sh` matches `ensure-issues-dir.sh` line-for-line in structure (shebang, set -euo pipefail, show_help, DIR variable, mkdir, echo).
- The report template uses Markdown tables for AC and test coverage evaluation to make pass/fail state scannable without re-reading the original issue.

## Tests Added or Updated

- `reviews/016-create-review-it-skill-review.md` — SMK-001: smoke test confirming the review report is produced with an overall verdict.

## Test Categories Not Applicable

- `Unit`: Not applicable — the skill is defined as Markdown documents; no executable unit to isolate.
- `Integration`: Not applicable — same reason.
- `E2E`: Not applicable — no browser or user journey.
- `Regression`: Not applicable — no prior defect.
- `Performance`: Not applicable — no throughput or latency constraint.
- `Security`: Not applicable — skill is read-only during review.
- `Observability`: Not applicable — no runtime instrumentation.

## Validation Run

```text
bash skills/review-it/scripts/ensure-reviews-dir.sh — passed (printed "ready: reviews")
find skills/review-it -type f | sort — all 5 required files present in correct directories
ls reviews/016-create-review-it-skill-review.md — file exists, overall verdict populated
```

## Accessibility Notes

Not applicable — this task does not change user-facing UI.

## Observability Changes

Not applicable — skill definition; no runtime to instrument.

## ADR Updates

Not applicable — this task does not touch architectural decisions.

## Unresolved Assumptions or Follow-Up

- The skill is not yet registered in `settings.json`. To make `/review-it` invocable from the harness, it needs to be added to the skill registry alongside `plan-it` and `implement-it`.
- AC-008 (missing issue file prompt) was verified by reading the skill files, not by live invocation without an argument. Confirm prompt behavior during first real usage.
