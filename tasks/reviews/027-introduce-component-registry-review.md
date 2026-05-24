---
id: "027"
issue: "tasks/issues/027-introduce-component-registry.md"
created: 2026-05-23
updated: 2026-05-23
---

# Review: Introduce component registry for adapters and evaluators

## Related Task

- `tasks/issues/027-introduce-component-registry.md`

## Overall Verdict

**Pass**

No Blocking findings. Two Suggestions are noted.

## Findings

| ID | Level | Requirement | Description | Evidence |
|----|-------|-------------|-------------|----------|
| F-001 | Non-blocking | Context / Use Case | `run.py`'s `_make_adapter()` still uses a hardcoded if-elif chain and raises `ValueError` for unknown platforms instead of delegating to `adapter_registry`. The issue Context states "bench-run --platform custom will delegate to the registry for unknown platform names" — this end-to-end behavior is not realized. No FR or AC explicitly requires `run.py` to consult the registry; the gap lives only in the narrative. | `benchmarks/run.py:43–50` |
| F-002 | Suggestion | AC-003 | The AC-003 test uses a fresh `Registry` instance (`custom_reg`) rather than calling `adapter_registry.register("gemini", ...)` as the AC text specifies. Underlying `Registry` behavior is correctly verified; the mismatch is cosmetic but means AC-003 is not tested verbatim against `adapter_registry`. | `benchmarks/tests/test_registry.py:131–143` |
| F-003 | Suggestion | IT-001 | IT-001 is titled "Runner resolves adapter by name through registry" but the runner receives adapters via DI — it never calls `adapter_registry.resolve()`. The test is correctly named `test_runner_resolves_evaluator_through_registry` and covers what the runner actually does (evaluator resolution). The IT-001 issue label creates a misleading expectation about adapter resolution. | `benchmarks/tests/test_registry.py:150`, `tasks/issues/027-introduce-component-registry.md:117–122` |

## AC Evaluation

| AC | Result | Notes |
|----|--------|-------|
| AC-001 | Pass | `harness/adapters/__init__.py` registers `"claude-code"` → `ClaudeCodeAdapter`; UT-005 resolves it and asserts `isinstance(instance, ClaudeCodeAdapter)`. |
| AC-002 | Pass | `registry.resolve()` raises `KeyError(f"Unknown component '{name}'. Known: {sorted(self._entries)}")` at `registry.py:31–33`; test `test_adapter_registry_unknown_raises_with_known_names` asserts all three names appear in the message. |
| AC-003 | Pass | `Registry.register()` + `resolve()` returns a `GeminiAdapter` instance in `test_custom_adapter_register_and_resolve`. See F-002 for the minor test-to-AC wording gap. |
| AC-004 | Pass | `registry.py:23–26` raises `ValueError` on duplicate name; `test_register_same_name_twice_raises_value_error` confirms it. |
| AC-005 | Pass | `grep` for `ClaudeCodeAdapter`, `PiAgentAdapter`, `OpenCodeAdapter` in `runner.py` returns no output. Evaluators are resolved exclusively via `evaluator_registry.resolve(task.evaluator)` at `runner.py:103`. |

## Test Coverage Evaluation

| Test Category | Status | Notes |
|---------------|--------|-------|
| Unit (UT-001 – UT-006) | Present | `benchmarks/tests/test_registry.py` — all six required unit tests present and asserting correct behavior. |
| Integration (IT-001) | Present | `benchmarks/tests/test_registry.py:150` — `test_runner_resolves_evaluator_through_registry` patches `evaluator_registry` and verifies the runner calls `resolve("behave")` and `resolve("plan")`. See F-003 for naming note. |
| Smoke | Not applicable | Registry is a pure in-memory module; no deployment boundary. |
| E2E | Not applicable | No user-visible CLI output changes. |
| Regression | Not applicable | No known previous defect. |
| Performance | Not applicable | O(1) dict lookup; no measurable overhead. |
| Security | Not applicable | Internal in-memory lookup; no external input or trust boundary. |
| Usability | Not applicable | `KeyError` message clarity verified by UT-002 / AC-002. |
| Observability | Not applicable | OBS-001 explicitly marked Not applicable in the issue. |

## Observability Evaluation

Not applicable — OBS-001 is explicitly Not applicable in the task; the registry is a pure in-memory lookup with no log, metric, or trace requirement.

## ADR Compliance

Not applicable — the task's Definition of Done does not require ADR updates. ADR 002 is listed as a pre-condition (must be `Accepted` before work starts), not as an artifact to update during this task.

## Convention Notes

- `F-002` — Suggestion — `test_custom_adapter_register_and_resolve` uses a fresh `Registry` instance to avoid polluting the global `adapter_registry` with a "gemini" entry across test runs. This is good test isolation practice, but it means the test doesn't match AC-003's exact "adapter_registry.register" wording. A follow-up could either update the AC to say "a Registry instance" or add an isolated adapter_registry invocation using `monkeypatch`/cleanup.
- `F-003` — Suggestion — IT-001's label in the issue says "adapter by name through registry" which doesn't match the runner's DI design (adapter is injected, not registry-resolved). Consider renaming the requirement to "evaluator_registry consulted by runner" for accuracy.

## Unresolved Assumptions or Follow-Up

- **F-001 follow-up**: `run.py:43–50` (`_make_adapter`) is the only remaining place where adapter selection is hardcoded outside the registry. Wiring `_make_adapter` to fall back to `adapter_registry.resolve(platform)` for unknown platforms would complete the pluggable-adapter use case described in the issue Context. This is out of scope for this task's ACs but worth tracking.
- NFR-002 (no transitive MLflow import from `harness.registry`) is verified at the code level: the base-class imports are guarded by `TYPE_CHECKING` at `registry.py:11–13`, so `harness.registry` pulls in only `typing` at runtime. No runtime check was run in this review session; the code evidence is sufficient.
