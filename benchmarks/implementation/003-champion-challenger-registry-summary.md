# Implementation Summary: Champion/Challenger Skill Variant Registry (Issue 014)

## Problem

After issue 013 tagged every summary run with a `skill_content_hash`, there was no tooling
to act on those hashes. Teams running multiple skill variants had no way to formally designate
a winner or compare variants side-by-side from the command line.

## Solution

Added two Click commands in `champion.py` that operate directly on the MLflow backend via
`MlflowClient`, with no coupling to internal tracker internals:

- **`bench-promote`** — sets `champion=true` on every summary run matching a given
  `skill_content_hash`, while atomically removing the tag from any previous champion.
- **`bench-compare`** — groups all summary runs for a skill by content hash, computes
  per-group mean metrics, sorts champion first then by F1 descending, and renders a Rich
  table. Prints a promotion hint when no champion has been designated.

## Files Changed

- **`champion.py`** (new) — implements `promote` and `compare` Click commands. Uses
  `MlflowClient` directly; no dependency on `harness.tracking.tracker`. The module-level
  `_MLRUNS_DIR` mirrors the pattern in `tracker.py` so the default URI resolves to the same
  local `mlruns/` directory.

- **`pyproject.toml`** — added two entry points:
  ```toml
  bench-promote = "champion:promote"
  bench-compare = "champion:compare"
  ```
  Used `champion:promote` (module-level, no package prefix) because `benchmarks/` has no
  `__init__.py`, which would make `benchmarks.champion:promote` unresolvable as an installed
  script.

- **`tests/test_champion.py`** (new) — five tests covering the core contract:
  - SMK-001: `promote` sets `champion=true` on the target run only
  - SMK-002: `compare` renders the champion row with `★ champion` label and correct hash
  - SMK-003: unknown hash exits with code 1 and prints the hash in the error message
  - NFR-002: promoting the same hash twice is idempotent (one champion, no duplicates)
  - AC-005: `compare` with no champion set includes a `bench-promote` usage hint

## Validation

```
champion imports: OK
5 passed in 1.13s
```

## Design Decisions

- `promote` accepts a `--tracking-uri` flag (consistent with `bench-run`) so tests can
  inject a temp backend without touching the real `mlruns/`.
- Champion transfer is atomic at the tag level: old champion tags are removed before the
  new champion tags are written. If the same hash is already champion, the delete loop
  skips it (run_id in target set), making the operation idempotent.
- Multiple platforms may share the same content hash (same skill files, different
  platforms). `promote` tags all of them; `compare` groups them together and sums their
  trial counts, giving a skill-wide view rather than a per-platform one.
- Rich truncates long strings in narrow terminals. The `test_compare_shows_champion_row`
  test sets `COLUMNS=200` via `CliRunner(env=...)` to ensure the full hash is visible
  in captured output.
- The `compare` command exits 0 even when no runs exist (prints a hint instead), matching
  the convention that query commands should not fail on empty results.
