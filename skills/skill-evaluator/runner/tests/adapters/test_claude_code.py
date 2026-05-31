import subprocess  # nosec B404
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from runner.adapters.claude_code import ClaudeCodeAdapter, _JudgePayload

_TIMEOUT_SECONDS = 12
_FAILURE_CODE = 2


def _adapter_without_init(tmp_path: Path) -> ClaudeCodeAdapter:
    adapter = ClaudeCodeAdapter.__new__(ClaudeCodeAdapter)
    adapter._skill_root = tmp_path
    adapter._timeout = _TIMEOUT_SECONDS
    adapter._claude_path = "claude"
    return adapter


def test_judge_payload_rejects_score_outside_unit_interval() -> None:
    # Arrange
    raw_payload = {"passed": True, "score": 1.2, "reasoning": "too high"}

    # Act / Assert
    with pytest.raises(ValidationError):
        _JudgePayload.model_validate(raw_payload)


def test_judge_payload_allows_missing_passed_flag() -> None:
    # Arrange
    raw_payload = {"score": 0.8, "reasoning": "good"}

    # Act
    payload = _JudgePayload.model_validate(raw_payload)

    # Assert
    assert payload.passed is None


def test_adapter_init_fails_when_claude_cli_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    which = Mock(return_value=None)
    monkeypatch.setattr("runner.adapters.claude_code.shutil.which", which)

    # Act / Assert
    with pytest.raises(RuntimeError, match="claude CLI not found"):
        ClaudeCodeAdapter(skill_root=tmp_path)
    which.assert_called_once_with("claude")


def test_load_skill_md_reads_expected_skill_file(tmp_path: Path) -> None:
    # Arrange
    skill_dir = tmp_path / "dataviz"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Use chart rules", encoding="utf-8")
    adapter = _adapter_without_init(tmp_path)

    # Act
    skill_text = adapter._load_skill_md("dataviz")

    # Assert
    assert skill_text == "Use chart rules"


def test_collect_dir_ignores_binary_files(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "chart.js").write_text("new Chart()", encoding="utf-8")
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe")
    adapter = _adapter_without_init(tmp_path)

    # Act
    files = adapter._collect_dir(tmp_path)

    # Assert
    assert files == {"chart.js": "new Chart()"}


def test_judge_defaults_passed_from_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        system=(
            "You are an expert evaluator of AI-generated software artifacts. "
            "Respond ONLY with a JSON object — no prose, no markdown fences: "
            '{"passed": <bool>, "score": <float 0.0-1.0>, '
            '"reasoning": <one sentence>}'
        ),
        model="sonnet",
        workdir=None,
        tools=None,
        append_system=False,
    )


def test_run_in_dir_raises_with_subprocess_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
    with pytest.raises(RuntimeError, match="claude exited 2"):
        adapter._run_in_dir(
            "prompt", system="system", model="haiku", workdir=None, tools=None
        )
    assert run.call_count == 1


def test_run_in_dir_passes_allowed_tools_and_workdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    adapter = _adapter_without_init(tmp_path)
    captured_cmd: list[str] = []
    captured_cwd = ""

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal captured_cmd, captured_cwd
        captured_cmd = cast(list[str], args[0])
        captured_cwd = cast(str, kwargs["cwd"])
        return subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout="ok", stderr=""
        )

    monkeypatch.setattr("runner.adapters.claude_code.subprocess.run", fake_run)

    # Act
    stdout = adapter._run_in_dir(
        "prompt", system="system", model="haiku", workdir=tmp_path, tools="Write Read"
    )

    # Assert
    assert stdout == "ok"
    assert "--allowedTools" in captured_cmd
    assert captured_cwd == str(tmp_path)
