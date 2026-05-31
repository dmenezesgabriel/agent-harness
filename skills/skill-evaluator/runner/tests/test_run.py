from unittest.mock import Mock

import pytest

from runner.models import CliArgs
from runner.run import _SKILLS_ROOT, _build_app, _parse_args


def test_parse_args_uses_invoke_as_default_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr("sys.argv", ["skill-eval", "--skill", "dataviz"])

    # Act
    args = _parse_args()

    # Assert
    assert args == CliArgs(skill="dataviz", mode="invoke")


def test_build_app_returns_composed_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    adapter_constructor = Mock(return_value=None)
    monkeypatch.setattr("runner.run.ClaudeCodeAdapter", adapter_constructor)

    # Act
    app = _build_app(CliArgs(mode="judge"))

    # Assert
    assert app.__class__.__name__ == "SkillEvaluationApp"
    adapter_constructor.assert_called_once_with(skill_root=_SKILLS_ROOT)


def test_build_app_does_not_construct_adapter_for_unused_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    adapter_constructor = Mock(return_value=None)
    monkeypatch.setattr("runner.run.ClaudeCodeAdapter", adapter_constructor)

    # Act
    _build_app(CliArgs(mode="invoke"))

    # Assert
    adapter_constructor.assert_called_once_with(skill_root=_SKILLS_ROOT)
