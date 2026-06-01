from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from runner.models import EvalOutcome, JudgeReport, Mode, ScenarioResult, TriggerReport


class ArtifactSet(BaseModel):
    """Files produced by one skill invocation.

    files maps relative paths (e.g. 'tasks/issues/001-foo.md') to contents.

    Usage:
        artifacts = ArtifactSet(workdir=Path('/tmp/run'))
        content = artifacts.get('tasks/issues/001-foo.md')
        issues = artifacts.matching('tasks/issues/*.md')
    """

    workdir: Path
    files: dict[str, str] = Field(default_factory=dict)

    def get(self, relative_path: str) -> str | None:
        return self.files.get(relative_path)

    def matching(self, glob: str) -> dict[str, str]:
        return {k: v for k, v in self.files.items() if Path(k).match(glob)}


class JudgeVerdict(BaseModel):
    rubric_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class AgentPort(Protocol):
    """Invoke a skill against a prompt and return the produced artifacts.

    Usage:
        adapter = ClaudeCodeAdapter(skill_root=Path('skills'))
        artifacts = adapter.invoke_skill('plan-it', 'Add login feature')
    """

    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet: ...


@runtime_checkable
class BaselineAgentPort(Protocol):
    """Invoke plain Claude (no skill injection) against a prompt.

    Used by compare mode to measure what Claude produces without skill guidance.

    Usage:
        adapter = ClaudeCodeAdapter(skill_root=Path('skills'))
        artifacts = adapter.invoke_baseline('Make a chart ...')
    """

    def invoke_baseline(self, prompt: str) -> ArtifactSet: ...


class TriggerClassifierPort(Protocol):
    """Classify whether an agent would invoke a skill for a given user message.

    Usage:
        triggered = classifier.classify(skill_description, 'plot my sales data')
    """

    def classify(self, skill_description: str, query: str) -> bool: ...


class JudgePort(Protocol):
    """Evaluate artifact content against a rubric string, return a verdict.

    Usage:
        verdict = judge.judge(artifact_content, rubric_text, rubric_id='context_relevance')
    """

    def judge(
        self, artifact_content: str, rubric: str, rubric_id: str
    ) -> JudgeVerdict: ...


class StructuralCheckPort(Protocol):
    """Run structural checks for one eval directory.

    Usage:
        results = structural_runner.run(evals_dir, artifacts_dir)
    """

    def run(self, evals_dir: Path, artifacts_dir: Path) -> list[ScenarioResult]: ...


class SkillInputSizerPort(Protocol):
    """Measure skill input sizes used for quality comparison.

    Usage:
        sizes = input_sizer.measure(Path('skills/dataviz/evals'))
    """

    def measure(self, evals_dir: Path) -> dict[str, int]: ...


class EvalModeStrategy(Protocol):
    """Run one evaluation mode and return a unified outcome.

    Usage:
        outcome = strategy.run('dataviz', evals_dir)
    """

    @property
    def mode(self) -> Mode: ...

    def run(self, skill_name: str, evals_dir: Path) -> EvalOutcome: ...


class ReportWriterPort(Protocol):
    """Write one skill evaluation report.

    Usage:
        report_path = writer.write('dataviz', evals_dir, 'all', [], [])
    """

    def write(
        self,
        skill_name: str,
        evals_dir: Path,
        mode: Mode,
        structural_results: list[ScenarioResult],
        judge_verdicts: list[JudgeReport],
        input_sizes: dict[str, int] | None = None,
        trigger_report: TriggerReport | None = None,
        baseline_structural_results: list[ScenarioResult] | None = None,
    ) -> Path: ...
