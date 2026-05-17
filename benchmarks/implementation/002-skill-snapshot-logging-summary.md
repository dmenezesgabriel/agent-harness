# Implementation Summary: Skill Snapshot Logging (Issue 013)

## Problem

Experiment runs had no way to tie a benchmark result back to the exact version of the skill
that produced it. If a skill's prompt files changed between runs, results were silently
incomparable. There was also no record of what the skill looked like at run time.

## Solution

Computed a deterministic sha256 content hash over every file in the skill directory and
attached it as an MLflow tag (`skill_content_hash`) on every trial run and on the summary
run. The summary run also uploads the full skill directory as an MLflow artifact set under
`skill_snapshot/`, giving a byte-perfect replay of the skill at benchmark time.

## Files Changed

- **`harness/skill_hash.py`** (new) — `compute_skill_hash(skill_dir)` walks the directory
  in sorted order, feeding `<relative_path>:<file_bytes>` into sha256, and returns
  `sha256:<first-16-hex-chars>`.

- **`harness/tracking/tracker.py`** — `log_trial` accepts `skill_content_hash: str | None`
  and writes it as a tag when present. `log_summary` accepts both `skill_content_hash` and
  `skill_snapshot_dir: Path | None`; sets the tag and calls `mlflow.log_artifacts` when the
  directory exists.

- **`harness/runner.py`** — imports `compute_skill_hash`; resolves `_skill_dir` from
  `skill_dir` argument or falls back to `_REPO_ROOT / "skills" / skill`; computes
  `skill_content_hash` once before the trial loop; threads both values through
  `log_trial` and `log_summary`.

- **`pyproject.toml`** — added `pytest>=8.0.0` to project dependencies so tests can be
  executed with `uv run python3 -m pytest`.

- **`tests/conftest.py`** (new) — inserts `benchmarks/` onto `sys.path` so test imports
  resolve correctly.

- **`tests/test_skill_hash.py`** (new) — four unit tests covering prefix format, length,
  determinism, change-on-file-modification, and change-on-file-addition.

## Validation

```
plan-it hash: sha256:69b18321735886f0   # deterministic, 23 chars total
skill_hash import: OK
tracker and runner imports: OK
4 passed in 0.01s
```

## Design Decisions

- Hash is computed once per `run_experiment` call (not per trial) — the skill is immutable
  during a single benchmark run, so this is correct and avoids redundant I/O.
- `_skill_dir` is a `Path` internally; the public `skill_dir` parameter remains `str | None`
  to preserve the existing CLI interface.
- `.pyc` and other binary artifacts inside the skill directory are included in the hash
  intentionally — the hash covers what is actually on disk, giving a full content fingerprint.
- Only the first 16 hex characters are used (64 bits of collision resistance), keeping the
  tag value short enough for MLflow UI display.
