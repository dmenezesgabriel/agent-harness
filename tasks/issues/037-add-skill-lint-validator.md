---
id: "037"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Add SkillLintValidator for zero-token structural pre-check

## Priority

P1 — Independent of tasks 035 and 036 (does not use TaskResult or RunSummary). Can be developed in parallel.

## Dependencies

- No task dependency; can start immediately.
- No ADR dependency; this is a new component with no cross-cutting architecture decisions.

## Assignability

**AFK** — The component interface, validation rules, and test coverage are fully specified.

## Context

Broken skill configurations — missing reference files, empty SKILL.md, broken `[name](references/foo.md)` links — are currently discovered only after burning agent tokens. A zero-token validator that runs before any adapter call catches these failures at the boundary where they're cheapest to fix.

`SkillLintValidator` is not an `Evaluator`: it validates the skill source directory (pre-execution), not agent output (post-execution). It lives in a dedicated module (`harness/skill_lint.py`) and is called from `run.py` before `run_experiment`.

## Use Cases

- **Feature**: Skill validation
- **Scenario**: Developer runs a benchmark with a misconfigured skill
- **Given** a skill directory where one `[references/planning-rules.md]` link is broken
- **When** the CLI runs before executing any adapter
- **Then** the validator reports the broken link with the file path and exits without consuming any agent tokens

## Definition of Ready

- The skill directory structure (SKILL.md + references/ + assets/) is known from the existing adapters.
- No dependency on task 035 or 036 model types.

## Functional Requirements

- `FR-001`: `SkillLintValidator.validate(skill_dir: Path) -> LintResult` where `LintResult` has a `skill: str`, `errors: list[LintError]`, and `passed: bool` property.
- `FR-002`: A `LintError` has `path: str` (relative to skill_dir) and `message: str`.
- `FR-003`: The validator fails with a descriptive `LintError` when `SKILL.md` does not exist in `skill_dir`.
- `FR-004`: The validator fails for each `[label](references/foo.md)` link in `SKILL.md` that resolves to a non-existent file.
- `FR-005`: The validator fails for each `[label](assets/bar.md)` link in `SKILL.md` that resolves to a non-existent file.
- `FR-006`: The validator passes silently when all linked files exist and `SKILL.md` is present.
- `FR-007`: `run.py` calls `SkillLintValidator().validate(skill_dir)` before `run_experiment`. If `lint_result.passed` is false, it prints each error and exits with code 1 without running any adapter.

## Non-Functional Requirements

- `NFR-001`: The validator makes no subprocess calls, no network calls, and no LLM calls. It reads only the local filesystem.
- `NFR-002`: `SkillLintValidator` does not import from `harness.adapters`, `harness.evaluators`, or `harness.tracking`. It has no dependency on the experiment pipeline.
- `NFR-003`: `LintResult` and `LintError` are plain dataclasses with no ABC inheritance.

## Observability Requirements

Not applicable — this is a pre-flight check with direct CLI output; no telemetry needed.

## Acceptance Criteria

- `AC-001`: **Given** a well-formed skill directory with all referenced files present, **When** `validate()` is called, **Then** `lint_result.passed == True` and `lint_result.errors == []`.
- `AC-002`: **Given** a skill directory with no `SKILL.md`, **When** `validate()` is called, **Then** `lint_result.passed == False` and `lint_result.errors` contains one error with `"SKILL.md"` in the message.
- `AC-003`: **Given** a `SKILL.md` with a link `[foo](references/missing-file.md)`, **When** `validate()` is called, **Then** `lint_result.errors` contains one error naming `references/missing-file.md`.
- `AC-004`: **Given** a `SKILL.md` with two broken links, **When** `validate()` is called, **Then** `lint_result.errors` has exactly two entries (one per broken link).
- `AC-005`: **Given** a broken skill, **When** `run.py` is invoked, **Then** it prints each `LintError.message` and exits with code 1 before calling the adapter.

## Required Tests

### Unit Tests

- `UT-001`: `validate()` on a clean skill dir (SKILL.md + all referenced files present) returns `LintResult(errors=[])`. Covers `FR-006`, `AC-001`.
- `UT-002`: `validate()` with missing `SKILL.md` returns one `LintError` mentioning `SKILL.md`. Covers `FR-003`, `AC-002`.
- `UT-003`: `validate()` with one broken `references/` link returns one `LintError` naming the missing file. Covers `FR-004`, `AC-003`.
- `UT-004`: `validate()` with one broken `assets/` link returns one `LintError` naming the missing file. Covers `FR-005`.
- `UT-005`: `validate()` with two broken links returns exactly two `LintError` entries. Covers `FR-004`, `AC-004`.
- `UT-006`: `SkillLintValidator` does not import `subprocess`, `harness.adapters`, `harness.evaluators`, or `harness.tracking`. Covers `NFR-001`, `NFR-002`.

### Integration Tests

- `IT-001`: **Scenario**: run.py exits early on lint failure  
  **Given** a skill directory with a broken reference link  
  **When** the CLI is invoked via `click.testing.CliRunner`  
  **Then** exit code is 1, the missing filename appears in output, and the adapter is never called  
  Covers `FR-007`, `AC-005`.

### Smoke Tests

Not applicable — no deploy or startup path changed.

### End-to-End Tests

Not applicable — no complete user journey changed.

### Regression Tests

Not applicable — no previously broken defect.

### Performance Tests

Not applicable — validator reads only local files; no performance constraint.

### Security Tests

Not applicable — no auth or trust boundary involved.

### Usability Tests

Not applicable — output is a developer-facing CLI error message; no UX component changed.

### Observability Tests

Not applicable — no telemetry introduced.

## Definition of Done

- `harness/skill_lint.py` exists with `LintError`, `LintResult`, `SkillLintValidator`.
- `SkillLintValidator` has zero imports from `harness.adapters`, `harness.evaluators`, `harness.tracking`.
- `run.py` calls the validator before `run_experiment`; exits with code 1 on failure.
- All unit and integration tests pass.
