---
id: "028"
task: "028-formalize-workspace-as-injectable-concern"
status: done
date: 2026-05-23
---

# Implementation: Formalize workspace isolation as an injectable concern

## Files changed

| File | Change |
|------|--------|
| `benchmarks/harness/adapters/workspace.py` | **Created** — `WorkspaceManager` ABC + `TempWorkspaceManager` |
| `benchmarks/tests/fakes/__init__.py` | **Created** — package marker |
| `benchmarks/tests/fakes/fake_workspace_manager.py` | **Created** — `FakeWorkspaceManager` with no production deps |
| `benchmarks/harness/adapters/claude_code.py` | **Refactored** — accepts `workspace_manager`; delegates workspace ops through it |
| `benchmarks/harness/adapters/pi_agent.py` | **Refactored** — same; removed `tempfile` import |
| `benchmarks/harness/adapters/opencode.py` | **Refactored** — same; removed `tempfile` import |
| `benchmarks/tests/test_workspace.py` | **Created** — 11 tests covering UT-001–UT-005 + IT-001 + FR-004 |

## Behavior implemented

- `WorkspaceManager` ABC defines three abstract methods: `init_workspace(task) -> Path`, `snapshot_workspace(path) -> dict[str, str]`, `cleanup(path) -> None`.
- `TempWorkspaceManager` wraps `_workspace.py` functions: creates a temp dir via `tempfile.mkdtemp()`, calls `_init_workspace()`, returns the path; delegates snapshot and cleanup to `_workspace.snapshot_workspace()` and `shutil.rmtree()`.
- `FakeWorkspaceManager` returns a caller-supplied `fixture_path`, records each path passed to `snapshot_workspace()` in `recorded_snapshots`, returns caller-supplied `snapshot_data`, is a no-op for `cleanup()`, and has zero production dependencies.
- All three adapters accept `workspace_manager: WorkspaceManager | None = None` in their constructor, defaulting to `TempWorkspaceManager()`. Their `run()` methods call `init_workspace` / `snapshot_workspace` / `cleanup` exclusively through `self.workspace_manager`, with cleanup in `finally` to ensure it runs on timeout too.

## Tests added

- `UT-001`: `FakeWorkspaceManager.init_workspace()` returns `fixture_path` and creates no real directory.
- `UT-002`: `FakeWorkspaceManager.snapshot_workspace()` appends the path to `recorded_snapshots` and returns `snapshot_data`.
- `UT-003`: `FakeWorkspaceManager.cleanup()` is a no-op and does not remove the directory.
- `UT-004`: `isinstance(TempWorkspaceManager(), WorkspaceManager)` is `True`.
- `UT-005`: `ClaudeCodeAdapter()` (default args) sets `workspace_manager` to a `TempWorkspaceManager` instance.
- `IT-001`: `ClaudeCodeAdapter` with `FakeWorkspaceManager` and subprocess mocked calls `init_workspace`, `snapshot_workspace`, and `cleanup` each once.
- Timeout coverage: adapter still calls `cleanup` when `subprocess.TimeoutExpired` is raised.
- FR-004 coverage: source scan confirms `FakeWorkspaceManager` contains no `subprocess`, `tempfile`, or `git` imports.

## Validations run

- `pytest tests/test_workspace.py` — 11/11 passed
- `pytest tests/` (excluding behave integration) — 48/48 passed, no regressions

## Accessibility checks

Not applicable — no UI touched.

## ADRs updated

Not applicable — ADR 002 (`extension-point-interface-mechanism`) already covers this pattern; `WorkspaceManager` is a conforming instance of it.

## Non-applicable test categories

- **Smoke tests**: No deploy or startup boundary; default behavior unchanged.
- **End-to-end tests**: No user-visible CLI behavior change.
- **Regression tests**: No known prior defect.
- **Performance tests**: Workspace delegation adds no measurable overhead.
- **Security tests**: No trust-boundary changes.
- **Usability tests**: No user-facing behavior change.
- **Observability tests**: Logging inside `_workspace.py` is unchanged and still active via `TempWorkspaceManager`.

## Unresolved assumptions

None.
