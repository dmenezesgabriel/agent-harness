---
id: "034"
issue: "tasks/issues/034-filter-skill-files-from-workspace-snapshot.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Filter skill scaffolding files from workspace snapshot

## Related Task

- `tasks/issues/034-filter-skill-files-from-workspace-snapshot.md`

## Overall Verdict

**Pass**

No Blocking findings. Implementation is correct and complete.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Suggestion | — | `from harness.models import Task` appears after the `__all__` declaration in `workspace.py`. PEP 8 places imports before module-level assignments; no functional impact. | `benchmarks/harness/adapters/workspace.py:13` |
| F-002 | Suggestion | — | `_StubWorkspaceManager` and `_SnapshotSequenceWorkspaceManager` allocate real temp directories via `tempfile.mkdtemp()` in `__init__` but never clean them up. Using `tempfile.TemporaryDirectory` as a context manager would prevent temp-dir leakage in the test suite. | `benchmarks/tests/test_opencode.py:81`, `benchmarks/tests/test_opencode.py:131` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `opencode.py:64` takes `before_snapshot` after scaffolding is copied; `opencode.py:84–85` diffs it against the post-agent snapshot. IT-001 at `test_opencode.py:155–176` asserts `skills/plan-it/SKILL.md` and `opencode.json` are absent from the result and `scaffold_files_filtered == 2`. |
| AC-002 | Pass | For `WITHOUT_SKILL`, `before_snapshot` stays `{}` (initialized at `opencode.py:54`) so `diff_workspace({}, after)` returns the full after-snapshot unchanged. `test_without_skill_snapshot_contains_all_agent_files` at `test_opencode.py:179–197` asserts `workspace_snapshot == agent_files` and `"scaffold_files_filtered" not in evaluator_details`. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001) | Present | `test_workspace.py:189–207` — two tests: `test_diff_workspace_returns_only_new_file` and `test_diff_workspace_empty_before_returns_all_after`. Both cover FR-001, FR-002. |
| Unit (UT-002) | Present | `test_workspace.py:214–231` — two tests: `test_diff_workspace_includes_modified_file` and `test_diff_workspace_unchanged_file_excluded`. Covers FR-003 (modified file included; unchanged excluded). |
| Integration (IT-001) | Present | `test_opencode.py:155–176` — `test_with_skill_snapshot_excludes_scaffold_files`. Uses `_SnapshotSequenceWorkspaceManager` to simulate before/after state and asserts scaffold files absent, `scaffold_files_filtered == 2`. Covers AC-001. |
| Integration (AC-002) | Present | `test_opencode.py:179–197` — `test_without_skill_snapshot_contains_all_agent_files`. Covers AC-002. |
| Smoke | Not applicable | No deploy behavior per issue. |
| E2E | Not applicable | No user journey per issue. |
| Regression | Not applicable | No previous defect per issue. |
| Performance | Not applicable | No performance impact per issue. |
| Security | Not applicable | No security surface per issue. |
| Usability | Not applicable | No user-facing change per issue. |

## Observability Evaluation

| OBS ID | Requirement | Status | Notes |
|--------|-------------|--------|-------|
| OBS-001 | Log count of filtered-out scaffolding files in `evaluator_details` or tracker metadata | Met | `opencode.py:91–92`: `if filtered_count: trial.evaluator_details["scaffold_files_filtered"] = filtered_count`. Key is absent when count is zero, consistent with test assertion at `test_opencode.py:197`. |

## ADR Compliance

Not applicable — no ADR dependencies listed in the task.

## Convention Notes

- `F-001` — Suggestion — `benchmarks/harness/adapters/workspace.py:13`: `from harness.models import Task` was already in the file before this task; adding `__all__` above it produces an unusual ordering where an import follows a module-level assignment. Cosmetic; no impact on behavior.
- `F-002` — Suggestion — `benchmarks/tests/test_opencode.py`: Both `_StubWorkspaceManager` and `_SnapshotSequenceWorkspaceManager` call `tempfile.mkdtemp()` directly with no cleanup. The `_StubWorkspaceManager` predates this task (from issue 032). Not introduced by this change, but the new `_SnapshotSequenceWorkspaceManager` repeats the same pattern.

## Unresolved Assumptions or Follow-Up

- `NFR-002` says "Works with all adapters" — the implementation satisfies this by exporting `diff_workspace` from `harness.adapters.workspace` (available to any adapter), but `ClaudeCodeAdapter` and `PiAdapter` do not yet apply it. This is not a gap in the current task scope (the issue says "Consider moving..." as a suggestion, not a requirement), but a follow-up task could apply the same before/after diff pattern to those adapters.
- The `filtered_count` calculation (`len(after_snapshot) - len(snapshot)`) counts files dropped from the after-snapshot but does not account for files present in `before` that were deleted by the agent. This edge case is not covered by the issue's ACs and is low-risk in practice; no finding raised.
