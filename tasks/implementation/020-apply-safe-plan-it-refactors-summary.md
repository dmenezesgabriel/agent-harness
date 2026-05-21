---
id: "020"
task: tasks/issues/020-apply-safe-plan-it-refactors.md
created: 2026-05-21
status: complete
---

# Implementation Summary: Apply safe plan-it refactors

## Files Changed

- `skills/plan-it-lean/` — created as a full copy of `skills/plan-it/` with four targeted edits applied

### Edits applied

| Change | File | Description |
|--------|------|-------------|
| P-2 | `references/output-files.md` lines 17–24 | Replaced 4-step prose algorithm with `bash scripts/next-issue-number.sh` invocation and fallback clause |
| P-3 | `SKILL.md` lines 43–81 | Stripped prose restatements from `Issue output requirement` and `ADR output requirement`; kept only `mkdir` commands |
| X-2 | `SKILL.md` lines 83–89 | Trimmed `Before marking complete` from 5 items to 1 (`CONTEXT.md` update reminder) |
| X-3 | `assets/adr-template.md` line 9 | Changed date placeholder from `<YYYY-MM-DD>` to `{{YYYY-MM-DD}}` |

## Behavior Implemented

- `skills/plan-it-lean/` is a token-efficient variant of `skills/plan-it/` that eliminates prose duplication in the skill body.
- Issue numbering delegates to the authoritative script rather than restating the algorithm in prose.
- Output requirement sections contain only the `mkdir` guard command; naming and ordering rules remain in `output-files.md` which step 12 already directs the agent to read.
- The `Before marking complete` checklist retains only the non-obvious `CONTEXT.md` update reminder.
- The ADR template date placeholder is standardized to mustache format (`{{YYYY-MM-DD}}`).

## Acceptance Criteria Verified

- **AC-001**: `output-files.md` issue numbering rule reads `bash scripts/next-issue-number.sh` invocation with fallback — confirmed by file diff.
- **AC-002**: `SKILL.md` `Issue output requirement` section contains only `mkdir -p tasks/issues` — confirmed.
- **AC-003**: `SKILL.md` `Before marking complete` contains exactly one item — confirmed.
- **AC-004**: `adr-template.md` line 9 is `{{YYYY-MM-DD}}` — confirmed.

## Tests Added or Updated

- `UT-001`: Not applicable — changes are pure text edits with no new logic.
- `IT-001` / `IT-002`: Benchmark variant run (`FR-006`, `FR-007`, `AC-005`) requires MLflow and model access; not run in this implementation step. Benchmark validation is a separate step per the Definition of Done.

## Validations Run

- File diffs confirmed all four edits applied correctly and no other content was modified.
- `NFR-001` satisfied: `skills/plan-it-lean/` is a full copy with only the four targeted changes.
- `NFR-002` satisfied: all preserved content (Good/Bad examples, rule text, cross-references, anti-patterns, final response) is verbatim.

## ADRs Updated

None — no architectural decisions involved (confirmed by task, which explicitly states no ADR dependency).

## Variant Hash

```
sha256:548d7edfb5bb765d
```

Computed via `harness.skill_hash.compute_skill_hash(Path("skills/plan-it-lean"))` (sha256 over sorted `<relative_path>:<file_content>` for every file in the directory, first 16 hex chars).

## Unresolved Assumptions / Follow-up

- `AC-005`, `AC-006`, `FR-006`, `FR-007`, `OBS-001`, `OBS-002`: Benchmark variant run and champion promotion require a model API endpoint and a running MLflow server. The development machine has ~120 MB free RAM; importing the benchmark dependencies (mlflow, scikit-learn, pandas) causes OOM. These steps must be run on a machine with sufficient memory using:
  ```
  uv run python benchmarks/run.py --skill plan-it --platform pi-agent --model openai-codex/gpt-5.4-mini --trials 5 --skill-dir ../skills/plan-it-lean
  ```
  Use the variant hash `sha256:548d7edfb5bb765d` to identify the run in MLflow and to invoke `bench-promote` if thresholds are met. If thresholds are met, update `skills/plan-it/` to match `skills/plan-it-lean/` and remove the variant directory.
