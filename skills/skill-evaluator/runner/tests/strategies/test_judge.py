from pathlib import Path
from typing import cast

from runner.exceptions import ProviderAbortError
from runner.judging import RubricJudgeRunner
from runner.models import JudgeReport
from runner.ports import JudgePort, JudgeVerdict, SkillInputSizerPort
from runner.strategies.judge import JudgeStrategy


class FakeJudgeRunner:
    def __init__(self, captured: list[Path], verdicts: list[JudgeReport]) -> None:
        self._captured = captured
        self._verdicts = verdicts

    def run(
        self, _evals_dir: Path, artifacts_dir: Path, _judge: object
    ) -> list[JudgeReport]:
        self._captured.append(artifacts_dir)
        return self._verdicts


class FailingJudgeRunner:
    def run(
        self, _evals_dir: Path, _artifacts_dir: Path, _judge: object
    ) -> list[JudgeReport]:
        raise ProviderAbortError("OpenCode timeout during judge")


class FakeJudge:
    def judge(self, _content: str, _rubric: str, rubric_id: str) -> JudgeVerdict:
        return JudgeVerdict(rubric_id=rubric_id, passed=True, score=0.9, reasoning="ok")


class FakeSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 200}


class TestJudgeStrategy:
    def test_judge_strategy_mode_is_judge(self) -> None:
        strategy = JudgeStrategy(
            cast(RubricJudgeRunner, FakeJudgeRunner([], [])),
            cast(JudgePort, FakeJudge()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        assert strategy.mode == "judge"

    def test_judge_strategy_prefers_generated_artifacts(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        generated_dir.mkdir(parents=True)
        captured: list[Path] = []

        strategy = JudgeStrategy(
            cast(RubricJudgeRunner, FakeJudgeRunner(captured, [])),
            cast(JudgePort, FakeJudge()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        strategy.run("dataviz", evals_dir)

        assert captured == [generated_dir]

    def test_judge_strategy_falls_back_to_golden(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        golden_dir = evals_dir / "fixtures" / "golden"
        golden_dir.mkdir(parents=True)
        captured: list[Path] = []

        strategy = JudgeStrategy(
            cast(RubricJudgeRunner, FakeJudgeRunner(captured, [])),
            cast(JudgePort, FakeJudge()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        strategy.run("dataviz", evals_dir)

        assert captured == [golden_dir]

    def test_judge_strategy_returns_verdicts(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        (evals_dir / "fixtures" / "golden").mkdir(parents=True)
        verdict = JudgeReport(
            rubric_id="quality", passed=True, score=0.9, reasoning="good"
        )

        strategy = JudgeStrategy(
            cast(RubricJudgeRunner, FakeJudgeRunner([], [verdict])),
            cast(JudgePort, FakeJudge()),
            cast(SkillInputSizerPort, FakeSizer()),
        )
        outcome = strategy.run("dataviz", evals_dir)

        assert outcome.mode == "judge"
        assert outcome.judge_verdicts == [verdict]
        assert outcome.structural_results == []

    def test_judge_strategy_reports_provider_abort(self, tmp_path: Path) -> None:
        evals_dir = tmp_path / "dataviz" / "evals"
        (evals_dir / "fixtures" / "golden").mkdir(parents=True)

        strategy = JudgeStrategy(
            cast(RubricJudgeRunner, FailingJudgeRunner()),
            cast(JudgePort, FakeJudge()),
            cast(SkillInputSizerPort, FakeSizer()),
        )

        outcome = strategy.run("dataviz", evals_dir)

        assert outcome.judge_verdicts[0].rubric_id == "judge_provider"
        assert outcome.judge_verdicts[0].passed is False
        assert "OpenCode timeout" in outcome.judge_verdicts[0].reasoning
