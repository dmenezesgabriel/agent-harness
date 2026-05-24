---
id: "034"
task: "034-filter-skill-files-from-workspace-snapshot"
status: done
date: 2026-05-23
---

# Implementation: Filter skill scaffolding files from workspace snapshot

## Files changed

- `benchmarks/harness/adapters/_workspace.py` — added `diff_workspace(before, after)` utility
- `benchmarks/harness/adapters/workspace.py` — exported `diff_workspace` via `__all__`
- `benchmarks/harness/adapters/opencode.py` — imported `diff_workspace`; updated `run()` to take a "before" snapshot after scaffolding is copied, diff it against the "after" snapshot, and log `scaffold_files_filtered` count
- `benchmarks/tests/test_workspace.py` — added UT-001 and UT-002 (4 tests for `diff_workspace`)
- `benchmarks/tests/test_opencode.py` — added IT-001 (2 integration tests: WITH_SKILL excludes scaffold files, WITHOUT_SKILL returns all agent files)

## Behavior implemented

**`diff_workspace(before, after)`** (in `_workspace.py`, exported from `workspace.py`): returns only entries from `after` that are either absent from `before` or have changed content. Files present with identical content in both are excluded.

**`OpenCodeAdapter.run()` changes**:
- For `WITH_SKILL` trials: takes a "before" snapshot immediately after scaffold files are copied (`opencode.json`, `skills/`), then a second snapshot after the agent exits, and calls `diff_workspace` to filter scaffolding out of `workspace_snapshot`.
- For `WITHOUT_SKILL` trials: `before_snapshot` is empty (`{}`), so `diff_workspace({}, after)` returns all agent-created files unchanged — no filtering applied.
- If any files were filtered, logs `scaffold_files_filtered: N` in `evaluator_details` (OBS-001).

## Tests added

| ID | File | Description |
|----|------|-------------|
| UT-001 | `test_workspace.py` | New file in "after" only is returned; empty "before" returns all "after" |
| UT-002 | `test_workspace.py` | Modified file (same path, different content) included; unchanged file excluded |
| IT-001 | `test_opencode.py` | WITH_SKILL snapshot excludes `skills/` and `opencode.json`; `scaffold_files_filtered=2` logged |
| AC-002 | `test_opencode.py` | WITHOUT_SKILL snapshot contains all agent files; no `scaffold_files_filtered` key |

## Validations run

- `pytest benchmarks/tests/` — 95/95 passed (6 pre-existing warnings, unrelated to this change)

## Accessibility checks

Not applicable — no UI touched.

## ADRs updated

None — this is a behavioral fix within an existing adapter, not an architectural decision.

## Non-applicable test categories

- SMK, E2E, REG, PT, ST, UX — as documented in the issue (no deploy, no user journey, no prior defect, no performance impact, no security surface, no user-facing change).

## Unresolved assumptions

None. The `_SnapshotSequenceWorkspaceManager` in `test_opencode.py` uses `iter()` over a list; tests that call `snapshot_workspace` more times than the list has entries would raise `StopIteration`. The production `TempWorkspaceManager` is not affected.
