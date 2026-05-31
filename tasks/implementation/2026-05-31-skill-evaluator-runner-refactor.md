# Skill Evaluator Runner Refactor

## Summary

Refactored the skill evaluator runner from one orchestration-heavy module into small ports/adapters-aligned modules. `runner/run.py` is now the composition root and CLI entrypoint, while evaluation workflow, discovery, invocation, structural checks, judging, reporting, and schemas live in focused modules.

## Requirements Verified

- Main runner function is small and delegates orchestration through `SkillEvaluationApp`.
- Responsibilities are split without adding inheritance, generic factories, or speculative abstractions.
- External boundaries remain behind ports/adapters: Claude CLI through `AgentPort`/`JudgePort`, Behave subprocess through `StructuralCheckPort`.
- Existing CLI behavior, report behavior, fixture paths, judge behavior, and exit-code semantics are preserved.
- Tests are redistributed by module and satisfy the existing test/module parity rule.
- Reports use timestamped filenames with microseconds to preserve multiple runs from the same day.
- Reports measure skill input size (`SKILL.md` and `fixtures/input_*.md`) instead of generated artifact output size, so quality can be compared against prompt/input size.

## Validation

- `uv run pytest`
- `uv run ruff format --check runner tests`
- `uv run ruff check runner tests`
- `uv run mypy`
- `uv run python scripts/check_test_module_parity.py`
- `uv run radon cc runner tests -n C`
- `uv run lint-imports`
- `uv run pytest --cov=runner --cov-fail-under=75`
- `make check`

## Not Applicable

- Accessibility checks: no UI or interactive frontend behavior changed.
- ADR update: this is an internal reversible refactor using the repo's existing ports/adapters direction.

## Unresolved Assumptions

- None.
