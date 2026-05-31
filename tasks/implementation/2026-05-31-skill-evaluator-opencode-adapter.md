---
id: "2026-05-31-skill-evaluator-opencode-adapter"
issue: "user-request"
created: 2026-05-31
updated: 2026-05-31
---

# Implementation Summary: Skill Evaluator OpenCode Adapter

## Related Task

- `user-request` — add an OpenCode SDK adapter alongside the Claude adapter.

## Files Changed

- `skills/skill-evaluator/runner/runner/adapters/opencode.py` — added the OpenCode SDK adapter, self-managed server lifecycle, artifact collection, and judge JSON parsing.
- `skills/skill-evaluator/runner/runner/models.py` — added CLI model fields for adapter selection and OpenCode provider/model defaults.
- `skills/skill-evaluator/runner/runner/run.py` — wired `--adapter claude|opencode` and OpenCode provider/model CLI/env options.
- `skills/skill-evaluator/runner/pyproject.toml` — added the pre-release `opencode-ai` SDK dependency.
- `skills/skill-evaluator/runner/uv.lock` — locked the OpenCode SDK dependency.
- `skills/skill-evaluator/runner/tests/adapters/test_opencode.py` — added OpenCode adapter tests with fake SDK/server boundaries.
- `skills/skill-evaluator/runner/tests/test_run.py` — added runner composition coverage for OpenCode adapter selection.

## Behavior Implemented

- The runner can use `--adapter opencode` while keeping Claude as the default adapter.
- OpenCode invocation starts `opencode serve` in a temporary workdir, calls the Python SDK, then collects generated text artifacts from that isolated workdir.
- OpenCode judge mode uses `openai-codex` with `chatgpt-5.5` by default and parses JSON verdicts into the existing `JudgeVerdict` contract.
- OpenCode skill invocation defaults to `openai-codex` with `gpt-5.4-mini`, with CLI and environment overrides for provider/model values.

## Design Notes

- The new adapter implements the existing `AgentPort` and `JudgePort`; orchestration code remains adapter-agnostic.
- The OpenCode server is owned by the adapter per request so live artifacts stay isolated like Claude tempdir artifacts.
- The SDK client is wrapped behind the adapter rather than leaking SDK types into ports or orchestration.
- Broader runner refactors were avoided; only adapter selection and model configuration were added.

## Tests Added or Updated

- `tests/adapters/test_opencode.py` — verifies CLI lookup failure, skill system prompt usage, artifact collection, judge score fallback, server cwd/termination, and missing assistant message errors.
- `tests/test_run.py` — verifies OpenCode adapter construction with the requested provider/model values and that Claude is not constructed when OpenCode is selected.

## Test Categories Not Applicable

- `E2E`: Not applicable — live OpenCode invocation requires external CLI credentials and real model access.
- `Performance`: Not applicable — this task adds adapter wiring and no performance-sensitive path.
- `Component`: Not applicable — this task changes only Python CLI/backend code.
- `Accessibility`: Not applicable — this task does not change user-facing UI, markup, keyboard behavior, or error states.

## Validation Run

```text
uv run pytest — passed, 43 tests
uv run ruff format --check runner tests scripts — passed
uv run ruff check runner tests scripts — passed
uv run mypy — passed
make check — passed, including coverage, deptry, vulture, radon, bandit, import-linter, and semgrep
```

## Accessibility Notes

- Not applicable — this task does not change frontend UI.

## Observability Changes

- Not applicable — no logging, metrics, traces, or analytics were required.

## ADR Updates

- Not applicable — this implementation follows the existing adapter/port architecture.

## Unresolved Assumptions or Follow-Up

- The default model IDs are configurable strings set to the requested values; a live OpenCode run should verify the exact model IDs exposed by the configured OpenCode provider registry.
