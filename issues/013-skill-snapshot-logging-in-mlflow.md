---
id: "013"
created: 2026-05-17
updated: 2026-05-17
status: active
---

# Task: Log skill snapshot and content hash to MLflow on every experiment run

## Priority

P0 — Required before champion/challenger comparison (Task 014) because the registry query is keyed by `skill_content_hash`.

## Dependencies

- No task dependency; can start immediately — all touch points are inside `benchmarks/harness/`.
- No ADR dependency; artifact upload and tag extensions are additive to the existing MLflow integration.

## Assignability

**AFK** — all requirements and acceptance criteria are resolved; no irreversible architectural decisions remain open.

## Context

When experimenting with skill variants, the benchmark runner currently has no record of which version of the skill files produced a given result. `skill_dir` is accepted as a free-form string tag but the actual files are never uploaded, and no content hash is computed. This means two runs labelled `plan-it` are indistinguishable in MLflow even if SKILL.md or any reference file changed between them.

The fix is to:
1. Compute a sha256 content hash over all files in the skill directory at run time.
2. Tag every trial run and the summary run with that hash.
3. Upload the full set of skill files as a `skill_snapshot/` artifact directory on the **summary run only** (uploading on every trial run would duplicate N×trials identical copies).

With the hash as a stable identifier, the champion/challenger registry (Task 014) can group runs by skill variant without requiring explicit version labels or directory copies.

## Use Cases

- **Feature**: Skill experiment traceability
- **Scenario**: Researcher modifies a reference file and re-runs the benchmark
- **Given** the researcher edits `skills/plan-it/references/output-files.md`
- **When** they run `uv run python run.py --skill plan-it --platform pi-agent`
- **Then** the new experiment's summary run in MLflow carries a different `skill_content_hash` tag and a `skill_snapshot/` artifact directory reflecting the edited file

## Definition of Ready

- `benchmarks/harness/tracking/tracker.py` and `benchmarks/harness/runner.py` are understood (read during planning).
- The skill directory structure (`SKILL.md`, `references/`, `assets/`, `scripts/`) is known.
- MLflow `mlflow.log_artifacts(local_dir, artifact_path)` is the upload API — no external service needed for file-backed tracking.

## Functional Requirements

- `FR-001`: `compute_skill_hash(skill_dir: Path) -> str` computes a sha256 digest over the concatenation of `<relative_path>:<file_content>` for every file in `skill_dir`, sorted by relative path. Returns the first 16 hex characters prefixed with `sha256:` (e.g. `sha256:a3f1b2c4d5e60712`).
- `FR-002`: `MLflowTracker.log_trial()` accepts a `skill_content_hash: str | None = None` parameter and adds it as an MLflow tag `skill_content_hash` when provided.
- `FR-003`: `MLflowTracker.log_summary()` accepts `skill_content_hash: str | None = None` and `skill_snapshot_dir: Path | None = None` parameters. When `skill_content_hash` is provided, it is added as a tag. When `skill_snapshot_dir` is provided, all files in that directory are uploaded under the `skill_snapshot/` artifact path.
- `FR-004`: `run_experiment()` in `runner.py` resolves the skill directory (from `skill_dir` parameter or the canonical `skills/<skill>/` path), calls `compute_skill_hash()` once before the trial loop, and passes the hash to every `tracker.log_trial()` and `tracker.log_summary()` call.
- `FR-005`: `compute_skill_hash()` and its helper live in a new module `benchmarks/harness/skill_hash.py`. No existing module is polluted.

## Non-Functional Requirements

- `NFR-001`: Hash computation must not read the same file more than once per experiment run.
- `NFR-002`: Artifact upload in `log_summary()` must use `mlflow.log_artifacts(str(local_dir), artifact_path="skill_snapshot")` so the directory tree is preserved.

## Observability Requirements

- `OBS-001`: The `skill_content_hash` tag must be visible on both trial runs and the summary run in the MLflow UI.
- `OBS-002`: The `skill_snapshot/` artifact directory on the summary run must contain the exact files that were in the skill directory at run time.

## Acceptance Criteria

- `AC-001`: **Given** a benchmark run completes, **When** any trial run is inspected in MLflow, **Then** it has a `skill_content_hash` tag whose value starts with `sha256:`.
- `AC-002`: **Given** two runs where any file in `skills/plan-it/` changed between them, **When** both summary runs are compared in MLflow, **Then** their `skill_content_hash` tags differ.
- `AC-003`: **Given** two runs where no skill file changed, **When** both summary runs are compared in MLflow, **Then** their `skill_content_hash` tags are identical.
- `AC-004`: **Given** a summary run in MLflow, **When** its artifacts are browsed, **Then** a `skill_snapshot/` directory exists and contains `SKILL.md` plus all files from `references/` and `assets/`.
- `AC-005`: **Given** `compute_skill_hash()` is called on a directory, **When** the same directory is passed again with no file changes, **Then** the returned hash is identical.

## Required Tests

### Unit Tests

- `UT-001`: Call `compute_skill_hash()` on a fixture directory with two known files; verify the returned hash is deterministic and starts with `sha256:`. Covers `FR-001`, `AC-005`.
- `UT-002`: Call `compute_skill_hash()` on the same fixture after modifying one file; verify the hash changes. Covers `AC-002`, `AC-003`.

### Integration Tests

Not applicable — the upload path requires a live MLflow tracking server and is adequately covered by the smoke test.

### Smoke Tests

- `SMK-001`: **Scenario**: Hash and snapshot appear after a dry-run experiment  
  **Given** a mock `MLflowTracker` that captures calls  
  **When** `run_experiment()` is called with one task and one trial  
  **Then** `log_trial()` was called with a non-empty `skill_content_hash`  
  **And** `log_summary()` was called with the same `skill_content_hash` and a valid `skill_snapshot_dir`  
  Covers `FR-002`, `FR-003`, `FR-004`.

### End-to-End Tests

Not applicable — covered by smoke test and existing MLflow file-backend in the benchmark run.

### Regression Tests

Not applicable — no prior defect to guard.

### Performance Tests

Not applicable — hash computation over a handful of small text files is negligible.

### Security Tests

Not applicable — skill files are local non-sensitive markdown; no trust boundary crossed.

### Usability Tests

Not applicable — no UI change.

### Observability Tests

- `OT-001`: After a real benchmark run, open the MLflow UI and confirm `skill_content_hash` appears in the Tags panel of both a trial run and the summary run. Covers `OBS-001`.
- `OT-002`: Browse the summary run artifacts and confirm `skill_snapshot/SKILL.md` exists and matches the local file. Covers `OBS-002`.

## Definition of Done

- `harness/skill_hash.py` exists with `compute_skill_hash()`.
- `tracker.py` `log_trial()` and `log_summary()` accept and use the new parameters.
- `runner.py` `run_experiment()` computes and propagates the hash.
- Unit tests (`UT-001`, `UT-002`) pass.
- Smoke test (`SMK-001`) passes.
- After a real run, `skill_content_hash` tag and `skill_snapshot/` artifact are visible in MLflow UI.
