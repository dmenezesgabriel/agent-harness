from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, computed_field

# Single pass line shared by judge verdicts (per-rubric score) and trigger
# routing (aggregate accuracy). One knob so "what counts as passing" can't drift
# between the two evaluation surfaces.
PASS_THRESHOLD = 0.7


class Mode(StrEnum):
    INVOKE = "invoke"
    JUDGE = "judge"
    ALL = "all"
    TRIGGER = "trigger"
    COMPARE = "compare"


AdapterName = Literal["claude", "opencode"]

# Single source for OpenCode provider/model defaults, shared by CliArgs, the CLI
# argument parser, and OpenCodeAdapter so the three layers cannot diverge.
DEFAULT_OPENCODE_INVOKE_PROVIDER = "openai-codex"
DEFAULT_OPENCODE_INVOKE_MODEL = "gpt-5.4-mini"
DEFAULT_OPENCODE_JUDGE_PROVIDER = "openai-codex"
DEFAULT_OPENCODE_JUDGE_MODEL = "chatgpt-5.4"


class CliArgs(BaseModel):
    skill: str | None = None
    mode: Mode = Mode.INVOKE
    adapter: AdapterName = "claude"
    input_fixture_limit: int = Field(default=2, ge=1)
    claude_timeout: int = 180
    opencode_invoke_provider: str = DEFAULT_OPENCODE_INVOKE_PROVIDER
    opencode_invoke_model: str = DEFAULT_OPENCODE_INVOKE_MODEL
    opencode_judge_provider: str = DEFAULT_OPENCODE_JUDGE_PROVIDER
    opencode_judge_model: str = DEFAULT_OPENCODE_JUDGE_MODEL
    opencode_timeout: int = 180


class ScenarioResult(BaseModel):
    feature: str
    scenario: str
    status: Literal["passed", "failed", "skipped"]
    failure: str | None = None


class JudgeReport(BaseModel):
    rubric_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ArtifactSelector(BaseModel):
    """Select a generated artifact for judge rubrics.

    Usage:
        selector = ArtifactSelector(path_patterns=["tasks/issues/*.md"])
    """

    extensions: list[str] = Field(default_factory=list)
    path_patterns: list[str] = Field(default_factory=list)
    exclude_path_patterns: list[str] = Field(default_factory=list)
    content_patterns: list[str] = Field(default_factory=list)
    prefer_largest: bool = True


class RubricDefinition(BaseModel):
    id: str
    artifact_file: str
    prompt: str
    artifact_section: str | None = None
    artifact_selector: ArtifactSelector | None = None


class RubricFile(BaseModel):
    rubrics: list[RubricDefinition] = Field(default_factory=list)


class TriggerResult(BaseModel):
    query: str
    expected: bool
    actual: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passed(self) -> bool:
        return self.expected == self.actual


class TriggerReport(BaseModel):
    results: list[TriggerResult]
    pass_rate: float
    passed: bool


class EvalOutcome(BaseModel):
    """Unified result bag returned by every evaluation mode strategy.

    Usage:
        outcome = strategy.run('dataviz', evals_dir)
        assert outcome.mode == Mode.INVOKE
    """

    mode: Mode
    structural_results: list[ScenarioResult] = Field(default_factory=list)
    baseline_structural_results: list[ScenarioResult] = Field(default_factory=list)
    judge_verdicts: list[JudgeReport] = Field(default_factory=list)
    baseline_judge_verdicts: list[JudgeReport] = Field(default_factory=list)
    trigger_report: TriggerReport | None = None
    input_sizes: dict[str, int] = Field(default_factory=dict)
