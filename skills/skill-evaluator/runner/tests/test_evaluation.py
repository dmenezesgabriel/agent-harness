from pathlib import Path
from typing import cast

from runner.discovery import SkillDiscovery
from runner.evaluation import SkillEvaluationApp, SkillEvaluator, _is_successful
from runner.models import CliArgs, EvalOutcome, JudgeReport, Mode, ScenarioResult
from runner.ports import EvalModeStrategy, ReportWriterPort

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

    def evaluate(self, _evals_dir: Path) -> bool:
        return self._is_success


class FakeStrategy:
    def __init__(self, outcome: EvalOutcome) -> None:
        self._outcome = outcome

    @property
    def mode(self) -> Mode:
        return self._outcome.mode

    def run(self, _skill_name: str, _evals_dir: Path) -> EvalOutcome:
        return self._outcome


class FakeReportWriter:
    def write(
        self,
        _skill_name: str,
        evals_dir: Path,
        _mode: Mode,
        _structural_results: list[ScenarioResult],
        _judge_verdicts: list[JudgeReport],
        _input_sizes: dict[str, int] | None = None,
        _trigger_report: object = None,
    ) -> Path:
        return evals_dir / "reports" / "report.md"


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


def test_evaluator_delegates_to_strategy_and_returns_success(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    evals_dir.mkdir(parents=True)
    outcome = EvalOutcome(
        mode="invoke",
        structural_results=[ScenarioResult(feature="f", scenario="s", status="passed")],
    )
    evaluator = SkillEvaluator(
        strategy=cast(EvalModeStrategy, FakeStrategy(outcome)),
        report_writer=cast(ReportWriterPort, FakeReportWriter()),
    )

    # Act
    is_success = evaluator.evaluate(evals_dir)

    # Assert
    assert is_success is True


def test_evaluator_returns_false_when_structural_check_fails(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    evals_dir.mkdir(parents=True)
    outcome = EvalOutcome(
        mode="invoke",
        structural_results=[ScenarioResult(feature="f", scenario="s", status="failed", failure="missing rule")],
    )
    evaluator = SkillEvaluator(
        strategy=cast(EvalModeStrategy, FakeStrategy(outcome)),
        report_writer=cast(ReportWriterPort, FakeReportWriter()),
    )

    # Act
    is_success = evaluator.evaluate(evals_dir)

    # Assert
    assert is_success is False


def test_evaluator_returns_false_when_judge_fails(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    evals_dir.mkdir(parents=True)
    outcome = EvalOutcome(
        mode="judge",
        judge_verdicts=[JudgeReport(rubric_id="q", passed=False, score=_FAILING_SCORE, reasoning="bad")],
    )
    evaluator = SkillEvaluator(
        strategy=cast(EvalModeStrategy, FakeStrategy(outcome)),
        report_writer=cast(ReportWriterPort, FakeReportWriter()),
    )

    # Act
    is_success = evaluator.evaluate(evals_dir)

    # Assert
    assert is_success is False


def test_is_successful_passes_when_all_checks_pass() -> None:
    outcome = EvalOutcome(
        mode="all",
        structural_results=[ScenarioResult(feature="f", scenario="s", status="passed")],
        judge_verdicts=[JudgeReport(rubric_id="r", passed=True, score=0.9, reasoning="good")],
    )
    assert _is_successful(outcome) is True


def test_is_successful_ignores_skipped_structural_results() -> None:
    outcome = EvalOutcome(
        mode="invoke",
        structural_results=[ScenarioResult(feature="f", scenario="s", status="skipped")],
    )
    assert _is_successful(outcome) is True
