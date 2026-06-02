import subprocess  # nosec B404
from pathlib import Path
from typing import cast
from unittest.mock import ANY, Mock

import pytest
from pydantic import ValidationError

from runner.adapters.claude_code import ClaudeCodeAdapter
from runner.adapters.contract import collect_text_artifacts
from runner.adapters.judge_payloads import JudgePayload
from runner.exceptions import ProviderAbortError

_TIMEOUT_SECONDS = 12
_FAILURE_CODE = 2


def _adapter_without_init(tmp_path: Path) -> ClaudeCodeAdapter:
    adapter = ClaudeCodeAdapter.__new__(ClaudeCodeAdapter)
    adapter._skill_root = tmp_path
    adapter._timeout = _TIMEOUT_SECONDS
    adapter._claude_path = "claude"
    return adapter


class TestJudgePayload:
    def test_judge_payload_rejects_score_outside_unit_interval(self) -> None:
        # Arrange
        raw_payload = {"passed": True, "score": 1.2, "reasoning": "too high"}

        # Act / Assert
        with pytest.raises(ValidationError):
            JudgePayload.model_validate(raw_payload)

    def test_judge_payload_allows_missing_passed_flag(self) -> None:
        # Arrange
        raw_payload = {"score": 0.8, "reasoning": "good"}

        # Act
        payload = JudgePayload.model_validate(raw_payload)

        # Assert
        assert payload.passed is None


class TestAdapterSetup:
    def test_adapter_init_fails_when_claude_cli_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        which = Mock(return_value=None)
        monkeypatch.setattr("runner.adapters.claude_code.shutil.which", which)

        # Act / Assert
        with pytest.raises(RuntimeError, match="claude CLI not found"):
            ClaudeCodeAdapter(skill_root=tmp_path)
        which.assert_called_once_with("claude")

    def test_load_skill_md_reads_expected_skill_file(self, tmp_path: Path) -> None:
        # Arrange
        skill_dir = tmp_path / "dataviz"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("Use chart rules", encoding="utf-8")
        adapter = _adapter_without_init(tmp_path)

        # Act
        skill_text = adapter._load_skill_md("dataviz")

        # Assert
        assert skill_text == "Use chart rules"

    def test_collect_dir_ignores_binary_files(self, tmp_path: Path) -> None:
        # Arrange
        (tmp_path / "chart.js").write_text("new Chart()", encoding="utf-8")
        (tmp_path / "image.bin").write_bytes(b"\xff\xfe")

        # Act
        files = collect_text_artifacts(tmp_path)

        # Assert
        assert files == {"chart.js": "new Chart()"}


class TestJudge:
    def test_judge_defaults_passed_from_score(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)

        run_in_dir = Mock(return_value='{"score": 0.8, "reasoning": "meets rubric"}')
        monkeypatch.setattr(adapter, "_run_in_dir", run_in_dir)

        # Act
        verdict = adapter.judge("artifact", "rubric", rubric_id="quality")

        # Assert
        assert verdict.passed is True
        assert verdict.score == 0.8
        assert verdict.rubric_id == "quality"
        run_in_dir.assert_called_once_with(
            "Rubric:\nrubric\n\nArtifact:\nartifact",
            system=ANY,
            model="sonnet",
            workdir=None,
            tools=None,
            operation="judge:quality",
            append_system=False,
        )


class TestClassify:
    def test_uses_haiku_model_and_returns_true_for_invoke(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)
        run_in_dir = Mock(return_value="INVOKE")
        monkeypatch.setattr(adapter, "_run_in_dir", run_in_dir)

        # Act
        result = adapter.classify("plan tasks and issues", "break down my feature")

        # Assert
        assert result is True
        run_in_dir.assert_called_once_with(
            "Skill description:\nplan tasks and issues\n\nUser message:\nbreak down my feature",
            system=ANY,
            model="haiku",
            workdir=None,
            tools=None,
            operation="classify",
            append_system=False,
        )

    def test_returns_false_for_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)
        monkeypatch.setattr(adapter, "_run_in_dir", Mock(return_value="SKIP"))

        # Act / Assert
        assert adapter.classify("plan tasks", "tell me a joke") is False


class TestInvokeBaseline:
    def test_calls_run_with_baseline_system_and_haiku(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)
        run_in_dir = Mock(return_value="")
        monkeypatch.setattr(adapter, "_run_in_dir", run_in_dir)

        # Act
        artifacts = adapter.invoke_baseline("Make a chart")

        # Assert
        assert run_in_dir.call_count == 1
        run_in_dir.assert_called_once_with(
            "Make a chart",
            system=ANY,
            model="haiku",
            workdir=ANY,
            tools="Bash,Read,Write",
            operation="baseline",
            append_system=False,
        )
        assert artifacts.files == {}


class TestRunInDir:
    def test_run_in_dir_raises_with_subprocess_preview(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)

        run = Mock(
            return_value=subprocess.CompletedProcess(
                args=["claude"],
                returncode=_FAILURE_CODE,
                stdout="bad stdout",
                stderr="bad stderr",
            )
        )

        monkeypatch.setattr("runner.adapters.claude_code.subprocess.run", run)

        # Act / Assert
        with pytest.raises(ProviderAbortError, match="ClaudeCode provider failure"):
            adapter._run_in_dir(
                "prompt",
                system="system",
                model="haiku",
                workdir=None,
                tools=None,
                operation="classify",
            )
        assert run.call_count == 1

    def test_run_in_dir_passes_allowed_tools_and_workdir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange
        adapter = _adapter_without_init(tmp_path)
        captured_cmd: list[str] = []
        captured_cwd = ""

        def fake_run(
            *args: object, **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            nonlocal captured_cmd, captured_cwd
            captured_cmd = cast(list[str], args[0])
            captured_cwd = cast(str, kwargs["cwd"])
            return subprocess.CompletedProcess(
                args=["claude"], returncode=0, stdout="ok", stderr=""
            )

        monkeypatch.setattr("runner.adapters.claude_code.subprocess.run", fake_run)

        # Act
        stdout = adapter._run_in_dir(
            "prompt",
            system="system",
            model="haiku",
            workdir=tmp_path,
            tools="Write Read",
            operation="invoke:dataviz",
        )

        # Assert
        assert stdout == "ok"
        assert "--allowedTools" in captured_cmd
        assert captured_cwd == str(tmp_path)

    def test_collect_dir_ignores_staged_skill_resources(self, tmp_path: Path) -> None:
        # Arrange
        (tmp_path / "scripts").mkdir(parents=True)
        (tmp_path / "scripts" / "render_task.py").write_text("script", encoding="utf-8")
        (tmp_path / "SKILL.md").write_text("skill", encoding="utf-8")
        (tmp_path / "tasks" / "issues").mkdir(parents=True)
        (tmp_path / "tasks" / "issues" / "001-task.md").write_text(
            "task", encoding="utf-8"
        )

        # Act
        files = collect_text_artifacts(tmp_path)

        # Assert
        assert files == {"tasks/issues/001-task.md": "task"}
