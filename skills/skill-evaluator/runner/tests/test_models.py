import pytest
from pydantic import ValidationError

from runner.models import JudgeReport, RubricFile

_INVALID_SCORE = 1.5


class TestRubricFile:
    def test_rubric_file_requires_artifact_file_and_prompt(self) -> None:
        # Arrange
        raw_rubric_file = {"rubrics": [{"id": "missing_prompt"}]}

        # Act / Assert
        with pytest.raises(ValidationError):
            RubricFile.model_validate(raw_rubric_file)


class TestJudgeReport:
    def test_judge_report_rejects_score_outside_unit_interval(self) -> None:
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            JudgeReport(
                rubric_id="palette",
                passed=False,
                score=_INVALID_SCORE,
                reasoning="too high",
            )
