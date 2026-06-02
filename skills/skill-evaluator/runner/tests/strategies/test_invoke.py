from pathlib import Path
from typing import cast

import pytest

from runner.exceptions import ProviderAbortError
from runner.invocation import SkillInvoker
from runner.models import ScenarioResult
from runner.ports import AgentPort, SkillInputSizerPort, StructuralCheckPort
from runner.strategies.invoke import InvokeStrategy


class FakeInvoker:
    def __init__(self, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir

    def invoke(self, _skill_name: str, _evals_dir: Path, _agent: object) -> Path:
        return self._artifacts_dir


class FailingInvoker:
    def invoke(self, _skill_name: str, _evals_dir: Path, _agent: object) -> Path:
        raise ProviderAbortError("OpenCode rate limit during invoke")


class FakeStructuralRunner:
    def __init__(self, results: list[ScenarioResult]) -> None:
        self._results = results

    def run(self, _evals_dir: Path, _artifacts_dir: Path) -> list[ScenarioResult]:
        return self._results


class FakeSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 100}


class FakeAgent:
    pass


class TestInvokeStrategy:
    def test_invoke_strategy_mode_is_invoke(self) -> None:
        strategy = InvokeStrategy(
            cast(SkillInvoker, FakeInvoker(Path("/tmp"))),  # nosec B108
            cast(StructuralCheckPort, FakeStructuralRunner([])),
            cast(AgentPort, FakeAgent()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        assert strategy.mode == "invoke"

    def test_invoke_strategy_returns_structural_results_and_input_sizes(
        self,
        tmp_path: Path,
    ) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)
        artifacts_dir = evals_dir / "fixtures" / "_generated_artifacts"
        artifacts_dir.mkdir(parents=True)
        passed = ScenarioResult(feature="f", scenario="s", status="passed")

        strategy = InvokeStrategy(
            cast(SkillInvoker, FakeInvoker(artifacts_dir)),
            cast(StructuralCheckPort, FakeStructuralRunner([passed])),
            cast(AgentPort, FakeAgent()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        outcome = strategy.run("dataviz", evals_dir)

        assert outcome.mode == "invoke"
        assert outcome.structural_results == [passed]
        assert outcome.input_sizes == {"SKILL.md": 100}
        assert outcome.judge_verdicts == []
        assert outcome.trigger_report is None

    def test_invoke_strategy_propagates_provider_abort(self, tmp_path: Path) -> None:
        # The strategy no longer shapes the failure; SkillEvaluator catches it.
        evals_dir = tmp_path / "dataviz" / "evals"
        evals_dir.mkdir(parents=True)

        strategy = InvokeStrategy(
            cast(SkillInvoker, FailingInvoker()),
            cast(StructuralCheckPort, FakeStructuralRunner([])),
            cast(AgentPort, FakeAgent()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        with pytest.raises(ProviderAbortError, match="OpenCode rate limit"):
            strategy.run("dataviz", evals_dir)
