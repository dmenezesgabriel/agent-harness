---
id: "014"
created: 2026-05-17
updated: 2026-05-17
status: active
---

# Task: Champion/challenger promotion and comparison CLI

## Priority

P1 — Depends on Task 013. Delivers the user-facing workflow for selecting the best skill variant after experiments produce comparable content hashes.

## Dependencies

- Depends on Task 013: `skill_content_hash` must exist as an MLflow tag on summary runs before this task can query or promote by hash.
- No ADR dependency; the champion tag is an MLflow tag extension and does not introduce a new storage system.

## Assignability

**HITL** — the decision of which skill variant is the champion is a human judgment call. The task automates the promotion mechanism and comparison view, but the human must inspect the comparison output and choose which content hash to promote.

## Context

After running several experiments with tweaked skill files, the researcher has a set of summary runs in MLflow, each tagged with a distinct `skill_content_hash`. There is no way to mark one variant as the accepted best ("champion") or to compare all variants side-by-side in a single view.

This task adds two CLI commands:

- **`bench-promote`** — marks a specific skill variant (identified by its content hash) as the champion for that skill by setting `champion=true` on its summary run and removing the tag from any previous champion.
- **`bench-compare`** — queries all summary runs for a skill, groups them by `skill_content_hash`, and prints a ranked table of metrics with the champion row highlighted.

The champion/challenger model is analogous to A/B testing in ML model registries: the champion is the current production skill; challengers are candidates. Researchers promote a challenger to champion when its metrics prove it is better.

## Use Cases

- **Feature**: Champion/challenger skill registry
- **Scenario**: Researcher promotes a better-performing skill variant to champion
- **Given** two experiments ran for `plan-it`, each with a different `skill_content_hash`
- **When** the researcher runs `bench-compare --skill plan-it` and sees variant B has higher `f1` and `behave_pass_rate`
- **Then** they run `bench-promote --skill plan-it --content-hash sha256:b2c3d4e5f6a70812` to mark variant B as champion
- **And** subsequent `bench-compare` output highlights variant B with a champion marker

- **Feature**: Champion/challenger skill registry
- **Scenario**: Re-running bench-compare after promotion
- **Given** a champion has been promoted
- **When** the researcher runs `bench-compare --skill plan-it`
- **Then** the champion row is marked distinctly and challengers are ranked below it by `f1` descending

## Definition of Ready

- Task 013 is complete: `skill_content_hash` appears as an MLflow tag on summary runs.
- The MLflow Python client `mlflow.MlflowClient` is available to set and delete tags on existing runs.
- `benchmarks/pyproject.toml` can register additional `[project.scripts]` entries.

## Functional Requirements

- `FR-001`: `bench-promote --skill <skill> --content-hash <hash>` queries all summary runs for the given skill across all platforms, finds the run whose `skill_content_hash` tag matches `<hash>`, sets `champion=true` on it, and removes `champion` from any run that previously held it.
- `FR-002`: If no summary run matches `<hash>`, the command exits with a clear error and a non-zero exit code.
- `FR-003`: `bench-compare --skill <skill>` queries all summary runs for the skill, groups by `skill_content_hash`, and renders a Rich table with columns: `hash (12 chars)`, `champion`, `platform`, `trials`, `behave_pass_rate (mean)`, `f1 (mean)`, `quality_score (mean)`, `latency_ms (mean)`.
- `FR-004`: In the `bench-compare` table, the champion row is highlighted (Rich `bold green`) and labelled `★ champion`. Challengers are ordered by `f1` descending.
- `FR-005`: If no champion is set for the skill, `bench-compare` prints a note: "No champion designated. Run `bench-promote --skill <skill> --content-hash <hash>` to set one."
- `FR-006`: Both commands live in `benchmarks/champion.py`. Both are registered in `pyproject.toml` as `bench-promote` and `bench-compare`.

## Non-Functional Requirements

- `NFR-001`: `bench-compare` must complete in under 10 seconds for up to 50 summary runs (standard MLflow file-backend query speed).
- `NFR-002`: Promoting a new champion must be idempotent — running `bench-promote` twice with the same hash produces the same final state.

## Observability Requirements

- `OBS-001`: After `bench-promote`, the MLflow UI must show `champion=true` on exactly one summary run per skill.
- `OBS-002`: `bench-compare` output must clearly identify which content hash is champion and which are challengers.

## Acceptance Criteria

- `AC-001`: **Given** two summary runs exist for `plan-it` with different `skill_content_hash` values, **When** `bench-promote --skill plan-it --content-hash <hash-A>` is run, **Then** run A has tag `champion=true` and run B has no `champion` tag.
- `AC-002`: **Given** run A is champion and `bench-promote` is called with `<hash-B>`, **When** the command completes, **Then** run B has `champion=true` and run A no longer has the `champion` tag.
- `AC-003`: **Given** at least two summary runs exist, **When** `bench-compare --skill plan-it` is run, **Then** the output table contains one row per distinct `skill_content_hash` with metric values populated.
- `AC-004`: **Given** a champion is set, **When** `bench-compare` renders the table, **Then** the champion row is visually distinct (bold green, `★ champion` label).
- `AC-005`: **Given** no champion is set, **When** `bench-compare` is run, **Then** output includes the promote command hint.
- `AC-006`: **Given** `bench-promote` is called with a hash that matches no summary run, **When** the command runs, **Then** it exits with code 1 and a message identifying the unknown hash.

## Required Tests

### Unit Tests

Not applicable — both commands are thin CLI wrappers over MLflow client calls; logic is fully covered by smoke tests.

### Integration Tests

Not applicable — requires a live MLflow backend; covered by smoke test with a file-backend fixture.

### Smoke Tests

- `SMK-001`: **Scenario**: Promote and verify champion tag  
  **Given** two synthetic summary runs logged to a temp MLflow file backend with distinct `skill_content_hash` tags  
  **When** `bench-promote --skill plan-it --content-hash <hash-A>` is invoked  
  **Then** run A has `champion=true` tag  
  **And** run B has no `champion` tag  
  Covers `FR-001`, `AC-001`.

- `SMK-002`: **Scenario**: Compare renders champion row  
  **Given** the same two runs with run A promoted  
  **When** `bench-compare --skill plan-it` is invoked  
  **Then** output contains `★ champion` on the hash-A row  
  **And** hash-B row appears without the champion marker  
  Covers `FR-003`, `FR-004`, `AC-003`, `AC-004`.

- `SMK-003`: **Scenario**: Promote with unknown hash exits non-zero  
  **Given** a temp MLflow backend with no summary run matching `sha256:ffffffffffffffff`  
  **When** `bench-promote --skill plan-it --content-hash sha256:ffffffffffffffff` is invoked  
  **Then** exit code is 1 and error message mentions the unknown hash  
  Covers `FR-002`, `AC-006`.

### End-to-End Tests

Not applicable — smoke tests cover the full command path against a real file backend.

### Regression Tests

Not applicable — no prior defect to guard.

### Performance Tests

- `PT-001`: Run `bench-compare` against a file backend with 50 synthetic summary runs and verify it completes in under 10 seconds. Covers `NFR-001`.

### Security Tests

Not applicable — CLI reads and writes local MLflow file backend; no trust boundary crossed.

### Usability Tests

Not applicable — CLI-only output; the Rich table is inherently self-documenting.

### Observability Tests

- `OT-001`: After `bench-promote`, open MLflow UI and confirm exactly one summary run for the skill shows `champion=true`. Covers `OBS-001`.

## Definition of Done

- `benchmarks/champion.py` exists with `bench-promote` and `bench-compare` Click commands.
- Both commands registered in `pyproject.toml` under `[project.scripts]`.
- Smoke tests `SMK-001`, `SMK-002`, `SMK-003` pass.
- `bench-compare` output is verified manually after at least two real experiment runs with different skill variants.
- No prior champion is silently left tagged after a new promotion.
