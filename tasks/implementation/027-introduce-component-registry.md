---
task: "027"
date: 2026-05-23
status: complete
---

# Implementation: Introduce component registry

## Files changed

| File | Change |
|------|--------|
| `benchmarks/harness/registry.py` | **Created** — `Registry[T]` class + `adapter_registry` and `evaluator_registry` singletons |
| `benchmarks/harness/adapters/__init__.py` | **Created** — registers `ClaudeCodeAdapter`, `PiAgentAdapter`, `OpenCodeAdapter` |
| `benchmarks/harness/evaluators/__init__.py` | **Created** — registers `PlanEvaluator`, `CodeEvaluator`, `BehaveEvaluator` |
| `benchmarks/harness/evaluators/behave_evaluator.py` | **Updated** — `BehaveEvaluator` now extends `Evaluator` ABC; `evaluate` signature accepts `task: Task` |
| `benchmarks/harness/runner.py` | **Updated** — removed `_EVALUATORS` dict, `_BEHAVE` singleton, and concrete evaluator imports; resolves evaluators via `evaluator_registry` |
| `benchmarks/tasks/plan-it/*.json` (5 files) | **Updated** — `"evaluator": "plan_evaluator"` → `"evaluator": "plan"` |
| `benchmarks/tasks/implement-it/*.json` (5 files) | **Updated** — `"evaluator": "code_evaluator"` → `"evaluator": "code"` |
| `benchmarks/tests/test_tracker.py` | **Updated** — patches `harness.runner.evaluator_registry` (mock) instead of removed `_EVALUATORS`/`_BEHAVE`; task fixture uses `"evaluator": "plan"` |
| `benchmarks/tests/test_registry.py` | **Created** — 11 unit and integration tests (UT-001–UT-006, AC-002, AC-003, AC-004, IT-001, extras) |

## Behavior implemented

- `Registry[T]` is a generic, O(1) dict-backed lookup. `register()` adds a no-arg factory; `resolve()` calls the factory and returns an instance; `list_names()` returns sorted names.
- Registering the same name twice raises `ValueError` (NFR-003).
- Resolving an unknown name raises `KeyError` whose message lists all known names (FR-006, AC-002).
- `adapter_registry` and `evaluator_registry` are module singletons created in `harness/registry.py` with no concrete class imports (FR-007).
- Built-in adapters and evaluators are registered in their package `__init__.py` files as side-effects on first import (FR-003, FR-004).
- `runner.py` resolves all evaluators exclusively through `evaluator_registry`; no hardcoded concrete class names remain in the runner's resolution path (FR-005, AC-005).
- Third parties can call `adapter_registry.register("custom", MyAdapter)` before invoking the runner; `bench-run --platform custom` will delegate to the registry for unknown platform names.

## Evaluator name migration

The canonical registry names are `"plan"`, `"code"`, `"behave"` (per task spec). All 10 task JSON files and the test fixture were updated from `"plan_evaluator"` / `"code_evaluator"` to `"plan"` / `"code"`.

## Tests added

| ID | Description |
|----|-------------|
| UT-001 | `register` then `resolve` returns factory output |
| UT-002 | `resolve("unknown")` raises `KeyError` with all names |
| UT-003 | `list_names()` returns sorted order |
| UT-004 | Registering the same name twice raises `ValueError` |
| UT-005 | `adapter_registry.resolve("claude-code")` returns `ClaudeCodeAdapter` |
| UT-006 | `evaluator_registry.resolve("plan")` returns `PlanEvaluator` |
| extra | `resolve("code")` → `CodeEvaluator`, `resolve("behave")` → `BehaveEvaluator` |
| AC-002 | `resolve("unknown-platform")` error message lists all adapter names |
| AC-003 | Custom adapter registered and resolved from a fresh registry |
| IT-001 | `BenchmarkRunner` resolves evaluator by name through registry |

## Validations run

- `uv run python -m pytest tests/ -x -q` — **39 passed** (28 pre-existing + 11 new), 0 failures
- NFR-002 verified: `import harness.registry` loads only stdlib typing modules; no MLflow or subprocess transitive imports
- AC-005 verified: `grep` on `runner.py` for concrete adapter/evaluator class names returns no output

## Accessibility checks

Not applicable — no UI touched.

## ADRs updated

None. Registry implementation is consistent with ADR 002 (`abc.ABC` extension points) — no architectural assumption changed.

## Non-applicable test categories

- **Smoke, E2E, regression, performance, security, usability, observability** — rationale matches task specification: registry is pure in-memory with no deployment boundary, no CLI output changes, no known defect, O(1) lookup, no external input, `KeyError` message clarity covered by UT-002/AC-002.

## Unresolved assumptions

None.
