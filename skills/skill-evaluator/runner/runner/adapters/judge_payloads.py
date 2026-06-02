"""Shared Pydantic models for parsing judge JSON responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

from runner.models import PASS_THRESHOLD, JudgeReport


class JudgePayload(BaseModel):
    passed: bool | None = None
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str

    def to_verdict(self, rubric_id: str) -> JudgeReport:
        return JudgeReport(
            rubric_id=rubric_id,
            passed=self.passed
            if self.passed is not None
            else self.score >= PASS_THRESHOLD,
            score=self.score,
            reasoning=self.reasoning,
        )


class CompareJudgePayload(BaseModel):
    """Response shape for a single compare_judge call covering both artifacts."""

    skill: JudgePayload
    baseline: JudgePayload

    def to_verdicts(self, rubric_id: str) -> tuple[JudgeReport, JudgeReport]:
        """Return (skill_verdict, baseline_verdict)."""
        return self.skill.to_verdict(rubric_id), self.baseline.to_verdict(rubric_id)
