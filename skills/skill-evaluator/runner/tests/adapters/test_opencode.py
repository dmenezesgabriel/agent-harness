from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from runner.adapters import opencode
from runner.adapters.opencode import OpenCodeAdapter, _JudgePayload

_TIMEOUT_SECONDS = 12


class FakeOpenCodeServer:
    active_workdir: ClassVar[Path | None] = None
    write_artifact: ClassVar[bool] = False

    def __init__(self, opencode_path: str, workdir: Path, port: int) -> None:
        self.opencode_path = opencode_path
        self.workdir = workdir
        self.port = port

    def __enter__(self) -> FakeOpenCodeServer:
        type(self).active_workdir = self.workdir
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        return None


class FakeSessionResource:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.chat_calls: list[dict[str, object]] = []

    def create(self) -> SimpleNamespace:
        return SimpleNamespace(id="session-1")

    def chat(self, session_id: str, **kwargs: object) -> SimpleNamespace:
        self.chat_calls.append({"session_id": session_id, **kwargs})
        if FakeOpenCodeServer.write_artifact:
            assert FakeOpenCodeServer.active_workdir is not None
            (FakeOpenCodeServer.active_workdir / "chart.js").write_text(
                "new Chart()", encoding="utf-8"
            )
        return SimpleNamespace(id="assistant-1")

    def messages(self, _session_id: str) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                info=SimpleNamespace(id="assistant-1"),
                parts=[SimpleNamespace(type="text", text=self.response_text)],
            )
        ]


class FakeOpenCodeClient:
    def __init__(self, response_text: str) -> None:
        self.session = FakeSessionResource(response_text)


class FakePopen:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, _timeout: int | None = None, **_kwargs: object) -> int:
        return 0

    def communicate(
        self, _timeout: int | None = None, **_kwargs: object
    ) -> tuple[str, str]:
        return "", ""


def _fake_client_factory(response_text: str) -> FakeOpenCodeClient:
    return FakeOpenCodeClient(response_text)


def _adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response_text: str = "ok"
) -> OpenCodeAdapter:
    monkeypatch.setattr(
        "runner.adapters.opencode.shutil.which", Mock(return_value="opencode")
    )
    monkeypatch.setattr("runner.adapters.opencode._OpenCodeServer", FakeOpenCodeServer)
    return OpenCodeAdapter(
        skill_root=tmp_path,
        timeout=_TIMEOUT_SECONDS,
        client_factory=lambda _base_url, _timeout: _fake_client_factory(response_text),
    )


class TestJudgePayload:
    def test_judge_payload_rejects_score_outside_unit_interval(self) -> None:
        raw_payload = {"passed": True, "score": 1.2, "reasoning": "too high"}

        with pytest.raises(ValidationError):
            _JudgePayload.model_validate(raw_payload)


class TestAdapterInit:
    def test_adapter_init_fails_when_opencode_cli_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        which = Mock(return_value=None)
        monkeypatch.setattr("runner.adapters.opencode.shutil.which", which)

        with pytest.raises(RuntimeError, match="opencode CLI not found"):
            OpenCodeAdapter(skill_root=tmp_path)
        which.assert_called_once_with("opencode")


class TestInvokeSkill:
    def test_invoke_skill_sends_skill_as_system_and_collects_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skill_dir = tmp_path / "dataviz"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("Use chart rules", encoding="utf-8")
        fake_client = FakeOpenCodeClient("ok")
        adapter = _adapter(tmp_path, monkeypatch)
        adapter._client_factory = lambda _base_url, _timeout: fake_client
        FakeOpenCodeServer.write_artifact = True

        try:
            artifacts = adapter.invoke_skill("dataviz", "Make a chart")
        finally:
            FakeOpenCodeServer.write_artifact = False

        assert artifacts.files == {"chart.js": "new Chart()"}
        assert fake_client.session.chat_calls[0]["system"] == "Use chart rules"
        assert fake_client.session.chat_calls[0]["provider_id"] == "openai-codex"
        assert fake_client.session.chat_calls[0]["model_id"] == "gpt-5.4-mini"

    def test_invoke_skill_ignores_dependency_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skill_dir = tmp_path / "dataviz"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("Use chart rules", encoding="utf-8")

        def fake_client_factory(_base_url: str, _timeout: int) -> FakeOpenCodeClient:
            assert FakeOpenCodeServer.active_workdir is not None
            (FakeOpenCodeServer.active_workdir / "node_modules" / "react").mkdir(
                parents=True
            )
            (
                FakeOpenCodeServer.active_workdir
                / "node_modules"
                / "react"
                / "index.js"
            ).write_text("library", encoding="utf-8")
            (FakeOpenCodeServer.active_workdir / "index.html").write_text(
                "<svg></svg>", encoding="utf-8"
            )
            return FakeOpenCodeClient("ok")

        adapter = _adapter(tmp_path, monkeypatch)
        adapter._client_factory = fake_client_factory

        artifacts = adapter.invoke_skill("dataviz", "Make a chart")

        assert artifacts.files == {"index.html": "<svg></svg>"}


class TestInvokeBaseline:
    def test_invoke_baseline_uses_neutral_system_and_collects_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_client = FakeOpenCodeClient("ok")
        adapter = _adapter(tmp_path, monkeypatch)
        adapter._client_factory = lambda _base_url, _timeout: fake_client
        FakeOpenCodeServer.write_artifact = True

        try:
            artifacts = adapter.invoke_baseline("Make a chart without skill guidance")
        finally:
            FakeOpenCodeServer.write_artifact = False

        assert artifacts.files == {"chart.js": "new Chart()"}
        assert fake_client.session.chat_calls[0]["system"] == opencode._BASELINE_SYSTEM
        assert fake_client.session.chat_calls[0]["provider_id"] == "openai-codex"
        assert fake_client.session.chat_calls[0]["model_id"] == "gpt-5.4-mini"


class TestClassify:
    def test_classify_returns_true_when_response_is_invoke(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = _adapter(tmp_path, monkeypatch, response_text="INVOKE")

        result = adapter.classify("Generates charts from data", "plot my sales data")

        assert result is True

    def test_classify_returns_false_when_response_is_skip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = _adapter(tmp_path, monkeypatch, response_text="SKIP")

        result = adapter.classify("Generates charts from data", "write a poem")

        assert result is False

    def test_classify_is_case_insensitive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = _adapter(tmp_path, monkeypatch, response_text="invoke")

        result = adapter.classify("Generates charts from data", "plot my sales data")

        assert result is True

    def test_classify_uses_judge_provider_and_model(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_client = FakeOpenCodeClient("INVOKE")
        adapter = _adapter(tmp_path, monkeypatch)
        adapter._client_factory = lambda _base_url, _timeout: fake_client

        adapter.classify("Generates charts from data", "plot my sales data")

        call = fake_client.session.chat_calls[0]
        assert call["system"] == opencode._CLASSIFY_SYSTEM
        assert call["provider_id"] == "openai-codex"
        assert call["model_id"] == "chatgpt-5.4"


class TestJudge:
    def test_judge_defaults_passed_from_score(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = _adapter(
            tmp_path,
            monkeypatch,
            response_text='{"score": 0.8, "reasoning": "meets rubric"}',
        )

        verdict = adapter.judge("artifact", "rubric", rubric_id="quality")

        assert verdict.passed is True
        assert verdict.score == 0.8
        assert verdict.rubric_id == "quality"


class TestOpenCodeServer:
    def test_opencode_server_starts_in_workdir_and_terminates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_popen = FakePopen()
        popen_constructor = Mock(return_value=fake_popen)
        monkeypatch.setattr(
            "runner.adapters.opencode.subprocess.Popen", popen_constructor
        )
        monkeypatch.setattr(
            "runner.adapters.opencode._server_is_ready", Mock(return_value=True)
        )

        with opencode._OpenCodeServer("opencode", tmp_path, 4321):
            pass

        assert fake_popen.terminated is True
        assert popen_constructor.call_args.kwargs["cwd"] == tmp_path


class TestAssistantText:
    def test_assistant_text_raises_when_message_is_missing(self) -> None:
        with pytest.raises(RuntimeError, match="assistant message 'missing'"):
            opencode._assistant_text([], "missing")

    def test_assistant_text_uses_latest_assistant_when_message_id_is_missing(
        self,
    ) -> None:
        messages = [
            SimpleNamespace(
                info=SimpleNamespace(id="user-1", role="user"),
                parts=[SimpleNamespace(type="text", text="prompt")],
            ),
            SimpleNamespace(
                info=SimpleNamespace(id="assistant-1", role="assistant"),
                parts=[SimpleNamespace(type="text", text="answer")],
            ),
        ]

        assert opencode._assistant_text(messages, None) == "answer"
