---
id: "037"
date: 2026-05-24
status: complete
---

# Implementation: Add SkillLintValidator

## Files changed

- `benchmarks/harness/skill_lint.py` — new module: `LintError`, `LintResult`, `SkillLintValidator`
- `benchmarks/run.py` — added `SkillLintValidator` import and pre-flight call before `run_experiment`
- `benchmarks/tests/test_skill_lint.py` — new test file: 10 tests covering all UT and IT cases

## Behavior implemented

- `SkillLintValidator.validate(skill_dir)` reads `SKILL.md` and resolves every `[label](references/…)` and `[label](assets/…)` link (stripping `#fragment` anchors before checking file existence).
- Returns `LintResult` with `skill`, `errors`, and `passed` property.
- `run.py` calls the validator after adapter construction, before `run_experiment`. On failure it prints each `LintError.message` and exits with code 1 — no adapter tokens consumed.

## Tests added

| ID | Description | Coverage |
|----|-------------|----------|
| UT-001 | Clean skill dir passes | FR-006, AC-001 |
| UT-002 | Missing `SKILL.md` → one error | FR-003, AC-002 |
| UT-003 | Broken `references/` link → one error | FR-004, AC-003 |
| UT-004 | Broken `assets/` link → one error | FR-005 |
| UT-005 | Two broken links → exactly two errors | FR-004, AC-004 |
| UT-006 | No forbidden imports in module source | NFR-001, NFR-002 |
| IT-001 | CLI exits with code 1; `run_experiment` never called | FR-007, AC-005 |
| + 3 | LintResult properties, no-links case | — |

## Validations run

- `pytest tests/` — **116 passed, 0 failed** (pre-existing suite + 10 new tests)

## Implementation note

The initial regex matched `references/foo.md#section` as a single path, causing false negatives on fragment-anchor links that are valid in Markdown. Fixed by stripping everything after `#` before the filesystem check. This matched the behavior of `skill_loader.py`, which silently ignores non-existent links but only resolves the base file path.

## Non-applicable test categories

- Smoke, E2E, regression, performance, security, usability, observability — as specified in the issue; validator reads only local filesystem with no external boundaries.

## ADRs updated

None — no new architectural pattern introduced; validator follows the existing module layout convention.
