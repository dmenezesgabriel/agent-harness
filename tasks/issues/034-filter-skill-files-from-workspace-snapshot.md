---
id: "034"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Filter skill scaffolding files from workspace snapshot

## Priority

P2 — Workspace snapshots contain 40+ pre-existing skill files that inflate the snapshot and make it hard to distinguish agent output from scaffolding.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this task changes a snapshot behavior within an existing adapter.

## Assignability

**AFK** — fully specified; requirements and acceptance criteria are resolved.

## Context

The `OpenCodeAdapter.run()` copies the entire `skills/` directory and `opencode.json` into the isolated workspace before the agent runs:

```python
if condition == Condition.WITH_SKILL:
    shutil.copy2(src_config, workspace / "opencode.json")
    shutil.copytree(src_skills, workspace / "skills")
```

After the agent completes, `WorkspaceManager.snapshot_workspace()` captures ALL files in the workspace directory — including these pre-existing scaffolding files. For plan-it tasks, this means a snapshot of ~44 files where only 1-2 are agent-created.

This pollutes:
- The `TrialResult.workspace_snapshot` dict, making it hard to find agent output
- Any evaluator that iterates over snapshot files (e.g., `CodeEvaluator` already filters `.py` files, but other consumers shouldn't need to know about internal scaffolding paths)

The fix should record which files were present before the agent ran (a "before" snapshot) and subtract them from the "after" snapshot, keeping only files the agent created or modified.

## Use Cases

- **Feature**: Workspace snapshot filtering
- **Scenario**: Developer debugs an agent's file output
- **Given** the agent ran with a skill in an isolated workspace
- **When** the snapshot is captured
- **Then** it should contain only files the agent created or modified, not skill scaffolding

## Definition of Ready

- The `TempWorkspaceManager` and `snapshot_workspace()` implementation are understood.
- The OpenCodeAdapter's workspace setup sequence is understood.

## Functional Requirements

- `FR-001`: Before the agent runs, capture a "before" snapshot of the workspace (list of file paths + content hashes).
- `FR-002`: After the agent completes, subtract the "before" files from the "after" snapshot, keeping only agent-created or agent-modified files.
- `FR-003`: The filtered snapshot must still include files the agent wrote inside subdirectories created by scaffolding (e.g., `docs/adrs/`).

## Non-Functional Requirements

- `NFR-001`: Zero false negatives — no agent-written file should be omitted from the filtered snapshot.
- `NFR-002`: Works with all adapters, not just OpenCode. Consider moving the diff logic into `TempWorkspaceManager.snapshot_workspace()` or adding a `diff_workspace(before, after)` utility method.

## Observability Requirements

- `OBS-001`: Log the count of filtered-out scaffolding files in `evaluator_details` or tracker metadata for debugging.

## Acceptance Criteria

- `AC-001`: **Given** a WITH_SKILL trial, **When** the snapshot is captured, **Then** the set of files differs from the full workspace contents by at most the agent's output files.
- `AC-002`: **Given** a WITHOUT_SKILL trial (which does not copy scaffold files), **When** the snapshot is captured, **Then** all files are agent-created (no filtering needed).

## Required Tests

### Unit Tests

- `UT-001`: Given a "before" list of files and an "after" list with one new file, verify the diff returns only the new file. Covers `FR-001`, `FR-002`.
- `UT-002`: Given a file present in both "before" and "after" but with different content, verify it is included in the diff (agent modified it). Covers `FR-003`.

### Integration Tests

- `IT-001`: **Scenario**: OpenCode adapter WITH_SKILL trial
  **Given** the OpenCode adapter runs a task WITH_SKILL
  **When** the snapshot is captured
  **Then** it does not contain `skills/` or `opencode.json` entries
  Covers `AC-001`.

### Not applicable

- `SMK-001`: Not applicable — no deploy behavior.
- `E2E-001`: Not applicable — no user journey.
- `REG-001`: Not applicable — no previous defect.
- `PT-001`: Not applicable — no performance impact.
- `ST-001`: Not applicable — no security impact.
- `UX-001`: Not applicable — no user-facing change.

## Definition of Done

- Workspace snapshot for OpenCode WITH_SKILL trials contains only agent-created/modified files.
- All existing tests pass.
- The change works across all adapters and does not break the `CodeEvaluator`'s snapshot-based code extraction.
