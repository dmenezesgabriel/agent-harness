import pytest
from pydantic import ValidationError

from runner.models import EvalQueriesFile, JudgeReport, RubricFile

_INVALID_SCORE = 1.5


class TestRubricFile:
    def test_rubric_file_requires_artifact_file_and_prompt(self) -> None:
        # Arrange
        raw_rubric_file = {"rubrics": [{"id": "missing_prompt"}]}

        # Act / Assert
        with pytest.raises(ValidationError):
            RubricFile.model_validate(raw_rubric_file)


class TestEvalQueriesFile:
    def test_parses_query_entries_with_optional_note(self) -> None:
        # Act
        parsed = EvalQueriesFile.model_validate_json(
            '{"should_trigger": [{"query": "make a chart", "note": "viz"}],'
            ' "should_not_trigger": [{"query": "fix my CSS"}]}'
        )

        # Assert
        assert parsed.should_trigger[0].query == "make a chart"
        assert parsed.should_trigger[0].note == "viz"
        assert parsed.should_not_trigger[0].note is None

    def test_rejects_entry_missing_query(self) -> None:
        with pytest.raises(ValidationError):
            EvalQueriesFile.model_validate({"should_trigger": [{"note": "no query"}]})


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
