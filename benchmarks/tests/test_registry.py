"""Unit and integration tests for the Registry class and built-in registrations.

Covers UT-001 through UT-006 and IT-001 from task 027.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from harness.registry import Registry, adapter_registry, evaluator_registry


# ---------------------------------------------------------------------------
# UT-001: register then resolve returns the factory's output
# ---------------------------------------------------------------------------

def test_register_and_resolve_returns_factory_output():
    reg: Registry[str] = Registry()
    reg.register("greeting", lambda: "hello")
    assert reg.resolve("greeting") == "hello"


# ---------------------------------------------------------------------------
# UT-002: resolve unknown name raises KeyError containing all registered names
# ---------------------------------------------------------------------------

def test_resolve_unknown_raises_key_error_with_known_names():
    reg: Registry[str] = Registry()
    reg.register("alpha", lambda: "a")
    reg.register("beta", lambda: "b")
    with pytest.raises(KeyError) as exc_info:
        reg.resolve("unknown")
    message = str(exc_info.value)
    assert "alpha" in message
    assert "beta" in message


# ---------------------------------------------------------------------------
# UT-003: list_names returns all registered names in sorted order
# ---------------------------------------------------------------------------

def test_list_names_returns_sorted():
    reg: Registry[str] = Registry()
    reg.register("zebra", lambda: "z")
    reg.register("apple", lambda: "a")
    reg.register("mango", lambda: "m")
    names = reg.list_names()
    assert names == sorted(names)
    assert set(names) == {"zebra", "apple", "mango"}


# ---------------------------------------------------------------------------
# UT-004: registering the same name twice raises ValueError
# ---------------------------------------------------------------------------

def test_register_same_name_twice_raises_value_error():
    reg: Registry[str] = Registry()
    reg.register("x", lambda: "first")
    with pytest.raises(ValueError):
        reg.register("x", lambda: "second")


# ---------------------------------------------------------------------------
# UT-005: adapter_registry resolves "claude-code" to a ClaudeCodeAdapter
# ---------------------------------------------------------------------------

def test_adapter_registry_resolves_claude_code():
    import harness.adapters  # ensure registration
    from harness.adapters.claude_code import ClaudeCodeAdapter

    assert "claude-code" in adapter_registry.list_names()
    assert "pi-agent" in adapter_registry.list_names()
    assert "opencode" in adapter_registry.list_names()

    with patch("shutil.which", return_value="/usr/bin/claude"):
        instance = adapter_registry.resolve("claude-code")
    assert isinstance(instance, ClaudeCodeAdapter)


# ---------------------------------------------------------------------------
# UT-006: evaluator_registry resolves "plan" to a PlanEvaluator
# ---------------------------------------------------------------------------

def test_evaluator_registry_resolves_plan():
    import harness.evaluators  # ensure registration
    from harness.evaluators.plan_evaluator import PlanEvaluator

    instance = evaluator_registry.resolve("plan")
    assert isinstance(instance, PlanEvaluator)


# ---------------------------------------------------------------------------
# Additional: evaluator_registry resolves "code" and "behave"
# ---------------------------------------------------------------------------

def test_evaluator_registry_resolves_code():
    import harness.evaluators
    from harness.evaluators.code_evaluator import CodeEvaluator

    instance = evaluator_registry.resolve("code")
    assert isinstance(instance, CodeEvaluator)


def test_evaluator_registry_resolves_behave():
    import harness.evaluators
    from harness.evaluators.behave_evaluator import BehaveEvaluator

    instance = evaluator_registry.resolve("behave")
    assert isinstance(instance, BehaveEvaluator)


# ---------------------------------------------------------------------------
# AC-002: unknown adapter raises KeyError containing all known names
# ---------------------------------------------------------------------------

def test_adapter_registry_unknown_raises_with_known_names():
    import harness.adapters
    with pytest.raises(KeyError) as exc_info:
        adapter_registry.resolve("unknown-platform")
    message = str(exc_info.value)
    assert "claude-code" in message
    assert "pi-agent" in message
    assert "opencode" in message


# ---------------------------------------------------------------------------
# AC-003: custom adapter registered and resolved
# ---------------------------------------------------------------------------

def test_custom_adapter_register_and_resolve(monkeypatch):
    import harness.adapters  # ensure built-in registration
    from harness.adapters.base import AgentAdapter

    class GeminiAdapter(AgentAdapter):
        name = "gemini"

        def run(self, task):
            ...

    # Snapshot _entries so the global adapter_registry is not permanently modified
    monkeypatch.setattr(adapter_registry, "_entries", dict(adapter_registry._entries))
    adapter_registry.register("gemini", GeminiAdapter)
    instance = adapter_registry.resolve("gemini")
    assert isinstance(instance, GeminiAdapter)


# ---------------------------------------------------------------------------
# IT-001: BenchmarkRunner resolves adapter through registry for run_experiment
# ---------------------------------------------------------------------------

def test_runner_resolves_evaluator_through_registry(tmp_path):
    """IT-001: runner uses evaluator_registry; evaluators resolved from task.evaluators."""
    import json
    from harness.runner import BenchmarkRunner
    from harness.tracking.null_tracker import NullTracker
    from harness.models import TaskResult

    null_tracker = NullTracker()

    fake_adapter = MagicMock()
    fake_adapter.name = "claude-code"
    fake_adapter.run.return_value = TaskResult(
        task_id="t-001",
        skill="plan-it",
        platform="claude-code",
        raw_output="output",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )

    fake_plan_ev = MagicMock()
    fake_plan_ev.evaluate.side_effect = lambda result, task: result
    fake_behave_ev = MagicMock()
    fake_behave_ev.evaluate.side_effect = lambda result, task: result

    skill_dir = tmp_path / "plan-it"
    skill_dir.mkdir()
    (skill_dir / "t-001.json").write_text(json.dumps({
        "id": "t-001",
        "skill": "plan-it",
        "title": "Test",
        "instruction": "Do something",
        "evaluator": "plan",
        "evaluators": ["plan", "behave"],
    }))

    mock_registry = MagicMock()
    mock_registry.resolve.side_effect = lambda name: (
        fake_behave_ev if name == "behave" else fake_plan_ev
    )

    runner = BenchmarkRunner(tracker=null_tracker)
    with patch("harness.runner.evaluator_registry", mock_registry):
        summary = runner.run_experiment(
            adapter=fake_adapter,
            skill="plan-it",
            tasks_dir=tmp_path,
        )

    assert summary.n_tasks == 1
    mock_registry.resolve.assert_any_call("plan")
    mock_registry.resolve.assert_any_call("behave")


# ---------------------------------------------------------------------------
# IT-001 (036): Runner applies evaluators in declared order
# ---------------------------------------------------------------------------

def test_runner_applies_evaluators_in_declared_order(tmp_path):
    """IT-001 (036): plan evaluator is called before behave evaluator on the same TaskResult."""
    import json
    from harness.runner import BenchmarkRunner
    from harness.tracking.null_tracker import NullTracker
    from harness.models import TaskResult

    call_order: list[str] = []

    fake_adapter = MagicMock()
    fake_adapter.name = "claude-code"
    fake_adapter.run.return_value = TaskResult(
        task_id="t-001",
        skill="plan-it",
        platform="claude-code",
        raw_output="output",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=5,
    )

    def make_ev(name):
        ev = MagicMock()
        ev.evaluate.side_effect = lambda result, task: (call_order.append(name), result)[1]
        return ev

    skill_dir = tmp_path / "plan-it"
    skill_dir.mkdir()
    (skill_dir / "t-001.json").write_text(json.dumps({
        "id": "t-001",
        "skill": "plan-it",
        "title": "Test",
        "instruction": "Do something",
        "evaluator": "plan",
        "evaluators": ["plan", "behave"],
    }))

    plan_ev = make_ev("plan")
    behave_ev = make_ev("behave")
    mock_registry = MagicMock()
    mock_registry.resolve.side_effect = lambda name: (
        behave_ev if name == "behave" else plan_ev
    )

    runner = BenchmarkRunner(tracker=NullTracker())
    with patch("harness.runner.evaluator_registry", mock_registry):
        runner.run_experiment(adapter=fake_adapter, skill="plan-it", tasks_dir=tmp_path)

    assert call_order == ["plan", "behave"]


# ---------------------------------------------------------------------------
# IT-002 (036): Runner skips behave for code-only evaluator list
# ---------------------------------------------------------------------------

def test_runner_skips_behave_for_code_only_task(tmp_path):
    """IT-002 (036): behave.evaluate is never called when task.evaluators == ['code']."""
    import json
    from harness.runner import BenchmarkRunner
    from harness.tracking.null_tracker import NullTracker
    from harness.models import TaskResult

    fake_adapter = MagicMock()
    fake_adapter.name = "claude-code"
    fake_adapter.run.return_value = TaskResult(
        task_id="impl-001",
        skill="implement-it",
        platform="claude-code",
        raw_output="output",
        latency_ms=50.0,
        input_tokens=5,
        output_tokens=5,
    )

    code_ev = MagicMock()
    code_ev.evaluate.side_effect = lambda result, task: result
    behave_ev = MagicMock()
    behave_ev.evaluate.side_effect = lambda result, task: result

    skill_dir = tmp_path / "implement-it"
    skill_dir.mkdir()
    (skill_dir / "impl-001.json").write_text(json.dumps({
        "id": "impl-001",
        "skill": "implement-it",
        "title": "Test",
        "instruction": "Implement X",
        "evaluator": "code",
        "evaluators": ["code"],
    }))

    mock_registry = MagicMock()
    mock_registry.resolve.side_effect = lambda name: (
        behave_ev if name == "behave" else code_ev
    )

    runner = BenchmarkRunner(tracker=NullTracker())
    with patch("harness.runner.evaluator_registry", mock_registry):
        runner.run_experiment(adapter=fake_adapter, skill="implement-it", tasks_dir=tmp_path)

    behave_ev.evaluate.assert_not_called()
