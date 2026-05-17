# Implementation Summary: Sandbox Benchmark Adapters (Issue 015)

## Problem

Benchmark adapters were writing skill output files (`issues/`, `docs/adrs/`,
`implementation/`) directly into the real repository directory instead of an
isolated workspace. This caused untracked file pollution across runs.

Root causes per adapter:
- `OpenCodeAdapter`: hardcoded `cwd=_REPO_ROOT`
- `ClaudeCodeAdapter`: no `cwd` — inherited caller's CWD
- `PiAgentAdapter`: used a temp dir CWD but no `git init`, so the pi CLI
  walked up to the real git tree and wrote files there

## Files Changed

### New

- `benchmarks/harness/adapters/_workspace.py`
  Shared module with two functions:
  - `init_workspace(workspace: Path) -> None` — runs `git init -q
    --initial-branch=main` and pre-creates `issues/`, `docs/adrs/`,
    `implementation/` subdirectories.
  - `snapshot_workspace(workspace: Path) -> dict[str, str]` — captures every
    file the agent wrote (excluding `scripts/` and `.git`), keyed by relative
    path.

### Modified

- `benchmarks/harness/adapters/pi_agent.py`
  - Removed inline `_snapshot_workspace` function (replaced by shared module).
  - Replaced manual `mkdir` loop with `init_workspace(workspace)`.
  - Changed `_snapshot_workspace(workspace)` call to `snapshot_workspace(workspace)`.

- `benchmarks/harness/adapters/claude_code.py`
  - Added `import tempfile`.
  - Added `from harness.adapters._workspace import init_workspace, snapshot_workspace`.
  - Wrapped subprocess call in `with tempfile.TemporaryDirectory() as tmp:`.
  - Added `init_workspace(workspace)` and `cwd=str(workspace)` to subprocess.
  - Collected `snapshot_workspace(workspace)` and threaded it into `_parse_stream`.
  - Added `workspace_snapshot` parameter to `_parse_stream` and passed it to
    `TrialResult`.

- `benchmarks/harness/adapters/opencode.py`
  - Added `import tempfile`.
  - Added `from harness.adapters._workspace import init_workspace, snapshot_workspace`.
  - Removed `_REPO_ROOT` (no longer needed).
  - Wrapped subprocess call in `with tempfile.TemporaryDirectory() as tmp:`.
  - Added `init_workspace(workspace)` and replaced `cwd=str(_REPO_ROOT)` with
    `cwd=str(workspace)`.
  - Collected `snapshot_workspace(workspace)` and threaded it into `_parse_output`.
  - Added `workspace_snapshot` parameter to `_parse_output` and passed it to
    `TrialResult`.

### Deleted

Leaked untracked files removed from the real repository:
- `docs/adrs/001-bull-redis-job-boundary.md`
- `docs/adrs/001-rate-limit-enforcement-and-keying.md`
- `docs/adrs/002-audit-log-storage-and-query-boundary.md`
- `docs/adrs/003-product-search-backend-decision.md`
- `docs/adrs/004-row-level-tenancy-resolution-and-scope.md`
- `docs/adrs/005-backwards-compatible-tenant-bootstrap-migration.md`
- `docs/adrs/` directory (emptied, then removed)

## Behavior Implemented

Every adapter now:
1. Creates a fresh `TemporaryDirectory` per trial.
2. Calls `init_workspace` to `git init` it and seed output subdirs — this
   stops the agent CLI from walking up the real git tree.
3. Runs the agent subprocess with `cwd=str(workspace)`.
4. Calls `snapshot_workspace` to capture written files before the temp dir is
   cleaned up.
5. Passes the snapshot into `TrialResult.workspace_snapshot`.

## Validation

```
uv run python3 -c "
from harness.adapters._workspace import init_workspace, snapshot_workspace
import tempfile, subprocess
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    ws = Path(tmp)
    init_workspace(ws)
    assert (ws / '.git').is_dir()
    assert (ws / 'issues').is_dir()
    assert (ws / 'docs/adrs').is_dir()
    assert (ws / 'implementation').is_dir()
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=str(ws),
                       capture_output=True, text=True)
    assert r.stdout.strip() == str(ws)
    print('All checks passed')
"
# → All checks passed

uv run python3 -c "
from harness.adapters.pi_agent import PiAgentAdapter
from harness.adapters.claude_code import ClaudeCodeAdapter
from harness.adapters.opencode import OpenCodeAdapter
print('imports OK')
"
# → imports OK
```
