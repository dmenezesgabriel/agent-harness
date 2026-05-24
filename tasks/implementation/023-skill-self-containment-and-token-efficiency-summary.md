---
id: "023"
issue: "tasks/issues/023-skill-self-containment-and-token-efficiency.md"
created: 2026-05-23
updated: 2026-05-23
---

# Implementation Summary: Skill self-containment and token efficiency

## Related Task

- `tasks/issues/023-skill-self-containment-and-token-efficiency.md`

## Files Changed

- `skills/plan-it/assets/adr-template.md` — removed "Related Tasks" section
- `skills/plan-it/references/adr-rules.md` — removed "Link the ADR to affected task files" from planning phase; removed "The ADR references the related task file" from Good examples
- `skills/implement-it/SKILL.md` — removed "use plan-it" from "When NOT to use"; condensed "Output requirement" → "Output files" with pointer to output-rules.md
- `skills/review-it/SKILL.md` — removed "use plan-it" and "use implement-it" from "When NOT to use"; condensed "Output requirement" → "Output files" with pointer to output-rules.md
- `skills/plan-it/SKILL.md` — merged "Issue output requirement" and "ADR output requirement" sections into single "Output files" section with pointer to output-files.md
- `skills/plan-it/assets/context-template.md` — replaced "Both plan-it and implement-it read it" with "Skills read it"
- `skills/implement-it/assets/context-template.md` — same fix
- `skills/review-it/assets/context-template.md` — same fix
- `scripts/install-skills.sh` — fixed `mapfile` array for remove command (was comma-joined string); simplified install to `--skill '*'` (tool naturally discovers only root-level skills, not `_deprecated`/`_on_revision`)

## Behavior Implemented

- ADR template no longer links to issue files; ADRs are standalone long-lived documents.
- ADR rules no longer instruct agents to back-link ADRs to task files; one-way reference (task → ADR) preserved.
- Loading implement-it or review-it alone reveals no references to sibling skills.
- `CONTEXT.md` template (all three skill copies) no longer names specific skills.
- plan-it SKILL.md reduced from 120 lines to ~102 lines by merging two output requirement sections (38 lines → ~9 lines).
- review-it and implement-it SKILL.md output sections similarly condensed.
- Install script now correctly propagates source skill edits to `.agents/skills/` on each run.

## Design Notes

- `--skill '*'` is safe for the install step: the `npx skills` tool discovers only `skills/implement-it`, `skills/plan-it`, `skills/review-it` (3 skills) because it does not descend into `_deprecated`/`_on_revision` subdirectories without `--full-depth`.
- `mapfile -t` replaced comma-joining to correctly pass skill names as separate shell words to `npx skills remove`.
- Condensed output sections retain the `mkdir -p` guards verbatim (NFR-002) and delegate naming rules to the existing reference files rather than duplicating examples.
- The one-way task → ADR link (tasks reference ADRs in Dependencies) is preserved; only the reverse direction was removed.

## Tests Added or Updated

- SMK-001: `grep -n "plan-it\|review-it" skills/implement-it/SKILL.md` → no output. Passed.
- SMK-002: `grep -n "plan-it\|implement-it" skills/review-it/SKILL.md` → no output. Passed.
- SMK-003: `grep -n "Related Tasks" skills/plan-it/assets/adr-template.md` → no output. Passed.
- SMK-004: `diff skills/implement-it/SKILL.md .agents/skills/implement-it/SKILL.md` → no diff. Passed.

## Test Categories Not Applicable

- `Unit`: Not applicable — all changes are Markdown files; no executable logic.
- `Integration`: Not applicable — no system boundaries crossed.
- `E2E`: Not applicable — no user-facing application.
- `Regression`: Not applicable — no prior defect being guarded.
- `Performance`: Not applicable — no runtime behavior.
- `Security`: Not applicable — no trust boundaries.
- `Usability`: Not applicable — no interactive UI.
- `Observability`: Not applicable — no logs, metrics, or traces.

## Validation Run

```text
grep SMK-001 through SMK-003 — passed (no matches found)
diff SMK-004 — passed (no diff between source and installed)
bash scripts/install-skills.sh — installed 3 skills successfully; deprecated skills not reinstalled
```

## Accessibility Notes

Not applicable — no UI changes.

## Observability Changes

Not applicable — Markdown-only changes.

## ADR Updates

Not applicable — no architectural decisions involved.

## Unresolved Assumptions or Follow-Up

- The `npx skills` tool's decision to exclude `_deprecated`/`_on_revision` from discovery is empirically confirmed but not documented in the tool's help text. If the tool changes behavior, the `--skill '*'` install may need revisiting.
