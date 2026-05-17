from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Condition(str, Enum):
    WITH_SKILL = "with_skill"
    WITHOUT_SKILL = "without_skill"


class Platform(str, Enum):
    API = "api"            # direct Anthropic API — controlled experiments
    CLAUDE_CODE = "claude-code"
    OPENCODE = "opencode"
    PI_AGENT = "pi-agent"


@dataclass
class GoldStandard:
    required_sections: list[str] = field(default_factory=list)
    required_findings: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    rubric: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    skill: str
    title: str
    instruction: str
    evaluator: str
    complexity: str = "single-file"
    language: str = "python"
    codebase_context: str = ""
    gold_standard: GoldStandard = field(default_factory=GoldStandard)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Task:
        gs_raw = d.get("gold_standard", {})
        gold_standard = GoldStandard(
            required_sections=gs_raw.get("required_sections", []),
            required_findings=gs_raw.get("required_findings", []),
            test_commands=gs_raw.get("test_commands", []),
            rubric=gs_raw.get("rubric", {}),
        )
        return cls(
            id=d["id"],
            skill=d["skill"],
            title=d["title"],
            instruction=d["instruction"],
            evaluator=d["evaluator"],
            complexity=d.get("complexity", "single-file"),
            language=d.get("language", "python"),
            codebase_context=d.get("codebase_context", ""),
            gold_standard=gold_standard,
            tags=d.get("tags", []),
        )


@dataclass
class TrialResult:
    task_id: str
    skill: str
    platform: str
    condition: str
    trial_index: int
    raw_output: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    # workspace snapshot: relative_path → file_content for every file the agent wrote
    workspace_snapshot: dict[str, str] = field(default_factory=dict)
    # evaluator outputs
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    quality_score: float = 0.0
    test_pass_rate: float = 0.0
    behave_pass_rate: float = 0.0
    behave_scenarios: dict[str, bool] = field(default_factory=dict)
    judge_score: float = 0.0
    judge_verdict: str = ""
    evaluator_details: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ExperimentSummary:
    skill: str
    platform: str
    n_tasks: int
    n_trials: int
    # aggregate metrics: mean ± std
    with_skill: dict[str, tuple[float, float]] = field(default_factory=dict)
    without_skill: dict[str, tuple[float, float]] = field(default_factory=dict)
    # statistical test results
    p_values: dict[str, float] = field(default_factory=dict)
    effect_sizes: dict[str, float] = field(default_factory=dict)
