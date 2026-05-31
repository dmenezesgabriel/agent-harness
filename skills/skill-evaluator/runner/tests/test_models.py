import pytest
from pydantic import ValidationError

from runner.models import RubricFile


def test_rubric_file_requires_artifact_file_and_prompt() -> None:
    # Arrange
    raw_rubric_file = {"rubrics": [{"id": "missing_prompt"}]}

    # Act / Assert
    with pytest.raises(ValidationError):
        RubricFile.model_validate(raw_rubric_file)
