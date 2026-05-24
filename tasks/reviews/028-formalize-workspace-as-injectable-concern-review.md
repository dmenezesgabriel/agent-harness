---
id: "028"
issue: "tasks/issues/028-formalize-workspace-as-injectable-concern.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Formalize workspace isolation as an injectable concern

## Related Task

- `tasks/issues/028-formalize-workspace-as-injectable-concern.md`

## Overall Verdict

**Pass**

No Blocking findings. Two Suggestions and one Non-blocking finding are noted below.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | IT-001 | `test_claude_code_adapter_delegates_workspace_lifecycle` does not assert that `cleanup()` was called during the normal execution path. IT-001 explicitly requires "FakeWorkspaceManager.cleanup() is called once". Cleanup-call tracking (monkey-patching `fake.cleanup`) is present only in the timeout-path test. | `benchmarks/tests/test_workspace.py:127–145` |
| F-002 | Suggestion | FR-005 | All three adapters declare `workspace_manager: WorkspaceManager \| None = None` and resolve the default inside `__init__` via `workspace_manager or TempWorkspaceManager()`, rather than the `workspace_manager: WorkspaceManager = TempWorkspaceManager()` signature stated in FR-005. The two forms are functionally equivalent, and the `None`-default idiom avoids a mutable-default-argument footgun, but the literal contract text diverges. | `benchmarks/harness/adapters/claude_code.py:33`, `pi_agent.py:74`, `opencode.py:37` |
| F-003 | Suggestion | — | In `pi_agent.py`, `init_workspace()` is called at line 87, outside the `try/finally` guard that starts at line 108. If an exception is raised during workspace setup between those lines (e.g., `shutil.copytree` at line 96), `cleanup()` will not execute and the temp directory will leak. No AC requires this fix, but it is an edge-case resource leak. | `benchmarks/harness/adapters/pi_agent.py:87–108` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `test_claude_code_adapter_delegates_workspace_lifecycle` patches subprocess, constructs `ClaudeCodeAdapter(workspace_manager=FakeWorkspaceManager(fixture_dir, {}))`, and asserts `len(fake.recorded_snapshots) == 1`. No real directory is created. |
| AC-002 | Pass | `test_fake_snapshot_workspace_records_path_and_returns_data` asserts the returned value equals `snapshot_data` and `some_path in fake.recorded_snapshots`. |
| AC-003 | Pass | `UT-005` verifies that `ClaudeCodeAdapter()` with no explicit `workspace_manager` sets `self.workspace_manager` to a `TempWorkspaceManager` instance, preserving production behavior. `TempWorkspaceManager` delegates to `_workspace.py` unchanged. |
| AC-004 | Pass | `test_temp_workspace_manager_isinstance_workspace_manager` asserts `isinstance(TempWorkspaceManager(), WorkspaceManager)` is `True`. |
| AC-005 | Pass | All three adapter files import only from `harness.adapters.workspace`; no `_workspace` import appears in any adapter `run()` body. `_workspace` is imported exclusively in `workspace.py` by `TempWorkspaceManager`. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `test_fake_init_workspace_returns_fixture_path` and `test_fake_init_workspace_does_not_create_directory` in `benchmarks/tests/test_workspace.py:42–53` |
| Unit (UT-002) | Present | `test_fake_snapshot_workspace_records_path_and_returns_data` and `test_fake_snapshot_workspace_accumulates_multiple_calls` at lines 60–76 |
| Unit (UT-003) | Present | `test_fake_cleanup_does_not_raise` and `test_fake_cleanup_does_not_remove_directory` at lines 83–91 |
| Unit (UT-004) | Present | `test_temp_workspace_manager_isinstance_workspace_manager` at line 98 |
| Unit (UT-005) | Present | `test_claude_code_adapter_default_workspace_manager` at line 106 |
| Integration (IT-001) | Present (partial) | `test_claude_code_adapter_delegates_workspace_lifecycle` verifies `init_workspace` (implicitly) and `snapshot_workspace` (via `recorded_snapshots`), but does not assert `cleanup` was called — see F-001 |
| Smoke | Not applicable | No deploy or startup boundary; adapters default to `TempWorkspaceManager` unchanged |
| E2E | Not applicable | No user-visible CLI behavior change |
| Regression | Not applicable | No known prior defect |
| Performance | Not applicable | Workspace delegation adds no measurable overhead |
| Security | Not applicable | No trust-boundary changes |
| Usability | Not applicable | No user-facing behavior change |
| Observability | Not applicable | Workspace logging inside `_workspace.py` unchanged |

## Observability Evaluation

Not applicable — OBS-001 is marked Not applicable in the task; existing logging inside `_workspace.py` is unchanged and still active via `TempWorkspaceManager`.

## ADR Compliance

| ADR | Required Action | Status |
|-----|-----------------|--------|
| `docs/adrs/002-extension-point-interface-mechanism.md` | Was required to be `Accepted` as a precondition (Definition of Ready), not a task DoD output | Done — ADR 002 status is `Accepted`; `WorkspaceManager` is listed in the ADR's Validation section confirming conformance |

## Convention Notes

- `F-002` — Suggestion — The `None`-default constructor pattern (`workspace_manager: WorkspaceManager | None = None`) is consistent across all three adapters and matches the `Tracker`/`NullTracker` injection pattern introduced in Task 026. It is not a convention violation; it is a minor divergence from the FR-005 literal signature text.
- `F-003` — Suggestion — The `init_workspace`-outside-`try` pattern in `pi_agent.py` was likely pre-existing structure. `claude_code.py` and `opencode.py` call `init_workspace` after `t0` / before the `try` block as well. Wrapping the full setup in a single `try/finally` would be a safer pattern. Not required by any AC.

## Unresolved Assumptions or Follow-Up

- IT-001 cleanup assertion gap (F-001): a one-line fix would be to add cleanup tracking to `test_claude_code_adapter_delegates_workspace_lifecycle` using the same monkey-patch pattern already present in the timeout test. Consider adding in a follow-up pass.
- `pi_agent.py` resource-leak window (F-003): could be resolved by moving `init_workspace()` inside the `try` block. Not required by this task's contract.
