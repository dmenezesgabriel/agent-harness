from unittest.mock import Mock

import pytest

from runner.models import CliArgs, Mode
from runner.run import _SKILLS_ROOT, _build_app, _parse_args


class TestParseArgs:
    def test_parse_args_uses_invoke_as_default_mode(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        monkeypatch.setattr("sys.argv", ["skill-eval", "--skill", "dataviz"])

        # Act
        args = _parse_args()

        # Assert
        assert args == CliArgs(skill="dataviz", mode=Mode.INVOKE)

    def test_parse_args_accepts_input_fixture_limit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        monkeypatch.setattr(
            "sys.argv",
            ["skill-eval", "--skill", "dataviz", "--input-fixture-limit", "3"],
        )

        # Act
        args = _parse_args()

        # Assert
        assert args.input_fixture_limit == 3


class TestBuildApp:
    def test_build_app_returns_composed_application(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        adapter_constructor = Mock(return_value=None)
        monkeypatch.setattr("runner.run.ClaudeCodeAdapter", adapter_constructor)

        # Act
        app = _build_app(CliArgs(mode=Mode.JUDGE))

        # Assert
        assert app.__class__.__name__ == "SkillEvaluationApp"
        adapter_constructor.assert_called_once_with(
            skill_root=_SKILLS_ROOT, timeout=180
        )

    def test_build_app_does_not_construct_adapter_for_unused_mode(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        adapter_constructor = Mock(return_value=None)
        monkeypatch.setattr("runner.run.ClaudeCodeAdapter", adapter_constructor)

        # Act
        _build_app(CliArgs(mode=Mode.INVOKE))

        # Assert
        adapter_constructor.assert_called_once_with(
            skill_root=_SKILLS_ROOT, timeout=180
        )

    def test_build_app_constructs_opencode_adapter_with_requested_models(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Arrange
        claude_constructor = Mock(return_value=None)
        opencode_constructor = Mock(return_value=None)
        monkeypatch.setattr("runner.run.ClaudeCodeAdapter", claude_constructor)
        monkeypatch.setattr("runner.run.OpenCodeAdapter", opencode_constructor)

        # Act
        _build_app(
            CliArgs(
                mode=Mode.INVOKE,
                adapter="opencode",
                opencode_invoke_provider="openai-codex",
                opencode_invoke_model="gpt-5.4-mini",
                opencode_judge_provider="openai-codex",
                opencode_judge_model="chatgpt-5.5",
            )
        )

        # Assert
        claude_constructor.assert_not_called()
        opencode_constructor.assert_called_once_with(
            skill_root=_SKILLS_ROOT,
            timeout=180,
            invoke_provider="openai-codex",
            invoke_model="gpt-5.4-mini",
            judge_provider="openai-codex",
            judge_model="chatgpt-5.5",
        )
