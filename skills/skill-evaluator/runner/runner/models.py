from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class Mode(StrEnum):
    INVOKE = "invoke"
    JUDGE = "judge"
    ALL = "all"
    TRIGGER = "trigger"
    COMPARE = "compare"


AdapterName = Literal["claude", "opencode"]


class CliArgs(BaseModel):
    skill: str | None = None
    mode: Mode = Mode.INVOKE
    adapter: AdapterName = "claude"
    opencode_invoke_provider: str = "openai-codex"
    opencode_invoke_model: str = "gpt-5.4-mini"
    opencode_judge_provider: str = "openai-codex"
    opencode_judge_model: str = "chatgpt-5.5"
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


class RubricDefinition(BaseModel):
    id: str
    artifact_file: str
    prompt: str
    artifact_section: str | None = None


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
