import pytest
from pydantic import ValidationError

from runner.adapters.judge_payloads import CompareJudgePayload, JudgePayload

_PASSING_SCORE = 0.8
_FAILING_SCORE = 0.5
_PASS_THRESHOLD = 0.7


class TestJudgePayload:
    def test_rejects_score_above_one(self) -> None:
        with pytest.raises(ValidationError):
            JudgePayload.model_validate({"score": 1.1, "reasoning": "x"})

    def test_rejects_negative_score(self) -> None:
        with pytest.raises(ValidationError):
            JudgePayload.model_validate({"score": -0.1, "reasoning": "x"})

    def test_allows_missing_passed_flag(self) -> None:
        payload = JudgePayload.model_validate(
            {"score": _PASSING_SCORE, "reasoning": "ok"}
        )
        assert payload.passed is None

    def test_to_verdict_uses_explicit_passed_when_present(self) -> None:
        payload = JudgePayload(passed=False, score=_PASSING_SCORE, reasoning="r")
        verdict = payload.to_verdict("r1")
        assert verdict.passed is False

    def test_to_verdict_derives_passed_from_score_above_threshold(self) -> None:
        payload = JudgePayload(score=_PASSING_SCORE, reasoning="r")
        verdict = payload.to_verdict("r1")
        assert verdict.passed is True

    def test_to_verdict_derives_failed_from_score_below_threshold(self) -> None:
        payload = JudgePayload(score=_FAILING_SCORE, reasoning="r")
        verdict = payload.to_verdict("r1")
        assert verdict.passed is False

    def test_to_verdict_sets_rubric_id(self) -> None:
        payload = JudgePayload(score=_PASSING_SCORE, reasoning="r")
        verdict = payload.to_verdict("my_rubric")
        assert verdict.rubric_id == "my_rubric"


class TestCompareJudgePayload:
    def test_to_verdicts_returns_skill_and_baseline(self) -> None:
        payload = CompareJudgePayload(
            skill=JudgePayload(passed=True, score=1.0, reasoning="skill ok"),
            baseline=JudgePayload(passed=False, score=0.3, reasoning="baseline weak"),
        )
        skill_v, baseline_v = payload.to_verdicts("my_rubric")
        assert skill_v.rubric_id == "my_rubric"
        assert skill_v.passed is True
        assert skill_v.score == 1.0
        assert baseline_v.rubric_id == "my_rubric"
        assert baseline_v.passed is False
        assert baseline_v.score == 0.3

    def test_rejects_invalid_skill_score(self) -> None:
        with pytest.raises(ValidationError):
            CompareJudgePayload.model_validate(
                {
                    "skill": {"score": 2.0, "reasoning": "x"},
                    "baseline": {"score": 0.5, "reasoning": "x"},
                }
            )
