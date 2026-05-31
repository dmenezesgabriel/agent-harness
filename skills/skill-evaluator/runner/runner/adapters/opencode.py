"""OpenCodeAdapter — invokes skills and judges via the OpenCode SDK."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess  # nosec B404
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Protocol, cast

from opencode_ai import Opencode
from pydantic import BaseModel, Field

from runner.ports import ArtifactSet, JudgeVerdict

_DEFAULT_TIMEOUT_SECONDS = 180
_SERVER_START_TIMEOUT_SECONDS = 10.0
_SERVER_POLL_SECONDS = 0.1
_JUDGE_PASS_THRESHOLD = 0.7
_ERROR_PREVIEW_CHARS = 500
_HOSTNAME = "127.0.0.1"
_INVOKE_PROVIDER = "openai-codex"
_INVOKE_MODEL = "gpt-5.4-mini"
_JUDGE_PROVIDER = "openai-codex"
_JUDGE_MODEL = "chatgpt-5.5"

_JUDGE_SYSTEM = (
    "You are an expert evaluator of AI-generated software artifacts. "
    "Respond ONLY with a JSON object - no prose, no markdown fences: "
    '{"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence>}'
)
_INVOKE_TOOLS = {"read": True, "write": True}


class _OpenCodeSession(Protocol):
    id: str


class _OpenCodeMessage(Protocol):
    id: str


class _OpenCodePart(Protocol):
    text: str


class _OpenCodeMessageWithParts(Protocol):
    info: _OpenCodeMessage
    parts: list[_OpenCodePart]


class _OpenCodeSessionResource(Protocol):
    def create(self) -> _OpenCodeSession: ...

    def chat(
        self,
        id: str,
        *,
        model_id: str,
        parts: list[dict[str, str]],
        provider_id: str,
        system: str,
        tools: dict[str, bool] | None,
        timeout: int,
    ) -> _OpenCodeMessage: ...

    def messages(self, id: str) -> object: ...


class _OpenCodeClient(Protocol):
    session: _OpenCodeSessionResource


class _JudgePayload(BaseModel):
    passed: bool | None = None
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class OpenCodeAdapter:
    """Run a skill or judge through a self-managed OpenCode server.

    Args:
        skill_root: Path to the skills/ directory.
        timeout: Seconds before SDK calls time out.

    Usage:
        adapter = OpenCodeAdapter(skill_root=Path('skills'))
        artifacts = adapter.invoke_skill('dataviz', 'Make a line chart ...')
    """

    def __init__(
        self,
        skill_root: Path,
        timeout: int = _DEFAULT_TIMEOUT_SECONDS,
        invoke_provider: str = _INVOKE_PROVIDER,
        invoke_model: str = _INVOKE_MODEL,
        judge_provider: str = _JUDGE_PROVIDER,
        judge_model: str = _JUDGE_MODEL,
        client_factory: Callable[[str, int], object] | None = None,
    ) -> None:
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            raise RuntimeError(
                "opencode CLI not found on PATH; install OpenCode before using "
                "adapter 'opencode'"
            )
        self._skill_root = skill_root
        self._timeout = timeout
        self._opencode_path = opencode_path
        self._invoke_provider = invoke_provider
        self._invoke_model = invoke_model
        self._judge_provider = judge_provider
        self._judge_model = judge_model
        self._client_factory = client_factory or _create_client

    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        skill_md = self._load_skill_md(skill_name)
        with tempfile.TemporaryDirectory(prefix=f"eval-{skill_name}-") as tmp:
            workdir = Path(tmp)
            self._chat_in_workdir(
                workdir,
                prompt,
                system=skill_md,
                provider_id=self._invoke_provider,
                model_id=self._invoke_model,
                tools=_INVOKE_TOOLS,
            )
            return ArtifactSet(workdir=workdir, files=self._collect_dir(workdir))

    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeVerdict:
        prompt = f"Rubric:\n{rubric}\n\nArtifact:\n{artifact_content}"
        with tempfile.TemporaryDirectory(prefix="eval-judge-") as tmp:
            stdout = self._chat_in_workdir(
                Path(tmp),
                prompt,
                system=_JUDGE_SYSTEM,
                provider_id=self._judge_provider,
                model_id=self._judge_model,
                tools=None,
            )
        payload = _JudgePayload.model_validate_json(stdout.strip())
        return JudgeVerdict(
            rubric_id=rubric_id,
            passed=payload.passed
            if payload.passed is not None
            else payload.score >= _JUDGE_PASS_THRESHOLD,
            score=payload.score,
            reasoning=payload.reasoning,
        )

    def _chat_in_workdir(
        self,
        workdir: Path,
        prompt: str,
        system: str,
        provider_id: str,
        model_id: str,
        tools: dict[str, bool] | None,
    ) -> str:
        port = _free_port()
        with _OpenCodeServer(self._opencode_path, workdir, port):
            client = cast(
                _OpenCodeClient,
                self._client_factory(f"http://{_HOSTNAME}:{port}", self._timeout),
            )
            session = client.session.create()
            message = client.session.chat(
                session.id,
                provider_id=provider_id,
                model_id=model_id,
                parts=[{"type": "text", "text": prompt}],
                system=system,
                tools=tools,
                timeout=self._timeout,
            )
            return _assistant_text(client.session.messages(session.id), message.id)

    def _collect_dir(self, workdir: Path) -> dict[str, str]:
        """Collect text files written by OpenCode to workdir."""
        files: dict[str, str] = {}
        for path in workdir.rglob("*"):
            if not path.is_file():
                continue
            with suppress(UnicodeDecodeError):
                files[str(path.relative_to(workdir))] = path.read_text(encoding="utf-8")
        return files

    def _load_skill_md(self, skill_name: str) -> str:
        path = self._skill_root / skill_name / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"SKILL.md not found for {skill_name!r} at {path}")
        return path.read_text(encoding="utf-8")


class _OpenCodeServer:
    def __init__(self, opencode_path: str, workdir: Path, port: int) -> None:
        self._opencode_path = opencode_path
        self._workdir = workdir
        self._port = port
        self._process: subprocess.Popen[str] | None = None

    def __enter__(self) -> _OpenCodeServer:
        self._process = subprocess.Popen(  # nosec B603
            [
                self._opencode_path,
                "serve",
                "--hostname",
                _HOSTNAME,
                "--port",
                str(self._port),
            ],
            cwd=self._workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._wait_until_ready()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        if self._process is None:
            return
        self._process.terminate()
        with suppress(subprocess.TimeoutExpired):
            self._process.wait(timeout=5)
            return
        self._process.kill()
        self._process.wait(timeout=5)

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + _SERVER_START_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise RuntimeError(self._server_exit_message())
            if _server_is_ready(self._port):
                return
            time.sleep(_SERVER_POLL_SECONDS)
        raise TimeoutError(
            f"opencode server on {_HOSTNAME}:{self._port} did not become ready "
            f"within {_SERVER_START_TIMEOUT_SECONDS} seconds"
        )

    def _server_exit_message(self) -> str:
        if self._process is None:
            return "opencode server process missing; expected running process"
        stdout, stderr = self._process.communicate(timeout=1)
        return (
            f"opencode serve exited {self._process.returncode} on port {self._port}\n"
            f"stderr: {stderr[:_ERROR_PREVIEW_CHARS]}\n"
            f"stdout: {stdout[:_ERROR_PREVIEW_CHARS]}"
        )


def _create_client(base_url: str, timeout: int) -> _OpenCodeClient:
    return cast(_OpenCodeClient, Opencode(base_url=base_url, timeout=timeout))


def _assistant_text(messages: object, message_id: str) -> str:
    for response_message in cast(list[_OpenCodeMessageWithParts], messages):
        if response_message.info.id != message_id:
            continue
        text_parts = [
            part.text
            for part in response_message.parts
            if getattr(part, "type", None) == "text"
        ]
        return "\n".join(text_parts)
    raise RuntimeError(
        f"assistant message {message_id!r} not found in OpenCode session messages; "
        "expected message with text parts"
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_socket:
        port_socket.bind((_HOSTNAME, 0))
        return int(port_socket.getsockname()[1])


def _server_is_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(  # nosec B310
            f"http://{_HOSTNAME}:{port}/global/health", timeout=1
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return False
    return payload.get("healthy") is True
