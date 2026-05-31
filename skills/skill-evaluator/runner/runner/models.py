from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["invoke", "judge", "all"]
AdapterName = Literal["claude", "opencode"]


class CliArgs(BaseModel):
    skill: str | None = None
    mode: Mode = "invoke"
    adapter: AdapterName = "claude"
    opencode_invoke_provider: str = "openai-codex"
    opencode_invoke_model: str = "gpt-5.4-mini"
    opencode_judge_provider: str = "openai-codex"
    opencode_judge_model: str = "chatgpt-5.5"


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
