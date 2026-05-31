from pathlib import Path
from typing import cast

from runner.discovery import SkillDiscovery
from runner.evaluation import SkillEvaluationApp, SkillEvaluator
from runner.invocation import SkillInvoker
from runner.judging import RubricJudgeRunner
from runner.models import CliArgs, JudgeReport, Mode, ScenarioResult
from runner.ports import AgentPort, JudgePort

_FAILING_SCORE = 0.2


class FakeDiscovery:
    def __init__(self, eval_dirs: list[Path]) -> None:
        self._eval_dirs = eval_dirs
        self.skills_root = Path("skills")

    def discover(self, _skill_filter: str | None) -> list[Path]:
        return self._eval_dirs


class FakeEvaluator:
    def __init__(self, is_success: bool) -> None:
        self._is_success = is_success

    def evaluate(self, _evals_dir: Path, _mode: Mode) -> bool:
        return self._is_success


class FakeInvoker:
    def invoke(self, _skill_name: str, evals_dir: Path, _agent: object) -> Path:
        return evals_dir / "fixtures" / "_generated_artifacts"


class FakeStructuralRunner:
    def run(self, _evals_dir: Path, _artifacts_dir: Path) -> list[ScenarioResult]:
        return [ScenarioResult(feature="f", scenario="s", status="passed")]


class FakeJudgeRunner:
    def run(
        self, _evals_dir: Path, _artifacts_dir: Path, _judge: object
    ) -> list[JudgeReport]:
        return [
            JudgeReport(
                rubric_id="quality", passed=False, score=_FAILING_SCORE, reasoning="bad"
            )
        ]


class FakeSkillInputSizer:
    def measure(self, _evals_dir: Path) -> dict[str, int]:
        return {"SKILL.md": 5}


class FakeReportWriter:
    def write(
        self,
        _skill_name: str,
        evals_dir: Path,
        _mode: Mode,
        _structural_results: list[ScenarioResult],
        _judge_verdicts: list[JudgeReport],
        _input_sizes: dict[str, int] | None = None,
    ) -> Path:
        return evals_dir / "reports" / "report.md"


class FakeAgent:
    pass


class FakeJudge:
    pass


def test_app_returns_failure_when_no_evals_are_found() -> None:
    # Arrange
    app = SkillEvaluationApp(
        cast(SkillDiscovery, FakeDiscovery([])),
        cast(SkillEvaluator, FakeEvaluator(is_success=True)),
    )

    # Act
    exit_code = app.run(CliArgs(skill="missing"))

    # Assert
    assert exit_code == 1


def test_app_returns_failure_when_any_skill_fails(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    app = SkillEvaluationApp(
        cast(SkillDiscovery, FakeDiscovery([evals_dir])),
        cast(SkillEvaluator, FakeEvaluator(is_success=False)),
    )

    # Act
    exit_code = app.run(CliArgs(mode="judge"))

    # Assert
    assert exit_code == 1


def test_evaluator_judge_mode_uses_generated_artifacts_when_present(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
    generated_dir.mkdir(parents=True)

    judged_dirs: list[Path] = []

    class CapturingJudgeRunner:
        def run(self, _evals_dir: Path, artifacts_dir: Path, _judge: object) -> list[JudgeReport]:
            judged_dirs.append(artifacts_dir)
            return []

    evaluator = SkillEvaluator(
        invoker=cast(SkillInvoker, FakeInvoker()),
        structural_runner=FakeStructuralRunner(),
        judge_runner=cast(RubricJudgeRunner, CapturingJudgeRunner()),
        input_sizer=FakeSkillInputSizer(),
        report_writer=FakeReportWriter(),
        agent=None,
        judge=cast(JudgePort, FakeJudge()),
    )

    # Act
    evaluator.evaluate(evals_dir, "judge")

    # Assert
    assert judged_dirs == [generated_dir]


def test_evaluator_judge_mode_falls_back_to_golden_when_no_generated(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    golden_dir = evals_dir / "fixtures" / "golden"
    golden_dir.mkdir(parents=True)

    judged_dirs: list[Path] = []

    class CapturingJudgeRunner:
        def run(self, _evals_dir: Path, artifacts_dir: Path, _judge: object) -> list[JudgeReport]:
            judged_dirs.append(artifacts_dir)
            return []

    evaluator = SkillEvaluator(
        invoker=cast(SkillInvoker, FakeInvoker()),
        structural_runner=FakeStructuralRunner(),
        judge_runner=cast(RubricJudgeRunner, CapturingJudgeRunner()),
        input_sizer=FakeSkillInputSizer(),
        report_writer=FakeReportWriter(),
        agent=None,
        judge=cast(JudgePort, FakeJudge()),
    )

    # Act
    evaluator.evaluate(evals_dir, "judge")

    # Assert
    assert judged_dirs == [golden_dir]


def test_evaluator_returns_false_when_judge_fails(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    evals_dir.mkdir(parents=True)
    evaluator = SkillEvaluator(
        invoker=cast(SkillInvoker, FakeInvoker()),
        structural_runner=FakeStructuralRunner(),
        judge_runner=cast(RubricJudgeRunner, FakeJudgeRunner()),
        input_sizer=FakeSkillInputSizer(),
        report_writer=FakeReportWriter(),
        agent=cast(AgentPort, FakeAgent()),
        judge=cast(JudgePort, FakeJudge()),
    )

    # Act
    is_success = evaluator.evaluate(evals_dir, "all")

    # Assert
    assert is_success is False
