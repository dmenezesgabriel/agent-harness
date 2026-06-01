from pathlib import Path

import pytest
from pydantic import ValidationError

from runner.ports import ArtifactSet, JudgeVerdict

_INVALID_SCORE = 1.5


class TestArtifactSet:
    def test_artifact_set_rejects_non_string_content(self) -> None:
        # Arrange
        raw_artifact_set = {"workdir": Path("run"), "files": {"chart.js": 12}}

        # Act / Assert
        with pytest.raises(ValidationError):
            ArtifactSet.model_validate(raw_artifact_set)

    def test_artifact_set_matches_files_by_glob(self) -> None:
        # Arrange
        artifacts = ArtifactSet(
            workdir=Path("run"),
            files={"charts/main.js": "chart", "notes/readme.md": "notes"},
        )

        # Act
        matches = artifacts.matching("charts/*.js")

        # Assert
        assert matches == {"charts/main.js": "chart"}


class TestJudgeVerdict:
    def test_judge_verdict_rejects_score_outside_unit_interval(self) -> None:
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            JudgeVerdict(
                rubric_id="palette",
                passed=False,
                score=_INVALID_SCORE,
                reasoning="too high",
            )
