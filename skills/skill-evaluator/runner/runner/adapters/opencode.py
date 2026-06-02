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

from runner.adapters.contract import (
    BASELINE_SYSTEM,
    CLASSIFY_SYSTEM,
    COMPARE_JUDGE_SYSTEM,
    INVOKE_TOOLS,
    JUDGE_SYSTEM,
    AdapterCall,
    build_classify_prompt,
    build_compare_judge_prompt,
    build_judge_prompt,
    classify_token,
    collect_text_artifacts,
)
from runner.adapters.judge_payloads import CompareJudgePayload, JudgePayload
from runner.models import JudgeReport
from runner.ports import ArtifactSet

_DEFAULT_TIMEOUT_SECONDS = 180
_SERVER_START_TIMEOUT_SECONDS = 10.0
_SERVER_POLL_SECONDS = 0.1
_HOSTNAME = "127.0.0.1"
_INVOKE_PROVIDER = "openai-codex"
_INVOKE_MODEL = "gpt-5.4-mini"
_JUDGE_PROVIDER = "openai-codex"
_JUDGE_MODEL = "chatgpt-5.4"
_ADAPTER_NAME = "OpenCode"


class _OpenCodeSession(Protocol):
    id: str


class _OpenCodeMessage(Protocol):
    id: str | None


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
            self._stage_skill_resources(skill_name, workdir)
            self._chat_in_workdir(
                workdir,
                prompt,
                system=skill_md,
                provider_id=self._invoke_provider,
                model_id=self._invoke_model,
                operation=f"invoke:{skill_name}",
                tools=_opencode_tools(),
            )
            return ArtifactSet(workdir=workdir, files=collect_text_artifacts(workdir))

    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeReport:
        prompt = build_judge_prompt(artifact_content, rubric)
        with tempfile.TemporaryDirectory(prefix="eval-judge-") as tmp:
            stdout = self._chat_in_workdir(
                Path(tmp),
                prompt,
                system=JUDGE_SYSTEM,
                provider_id=self._judge_provider,
                model_id=self._judge_model,
                operation=f"judge:{rubric_id}",
                tools=None,
            )
        return JudgePayload.model_validate_json(stdout.strip()).to_verdict(rubric_id)

    def compare_judge(
        self,
        skill_content: str,
        baseline_content: str,
        rubric: str,
        rubric_id: str,
    ) -> tuple[JudgeReport, JudgeReport]:
        prompt = build_compare_judge_prompt(skill_content, baseline_content, rubric)
        with tempfile.TemporaryDirectory(prefix="eval-compare-judge-") as tmp:
            stdout = self._chat_in_workdir(
                Path(tmp),
                prompt,
                system=COMPARE_JUDGE_SYSTEM,
                provider_id=self._judge_provider,
                model_id=self._judge_model,
                operation=f"compare_judge:{rubric_id}",
                tools=None,
            )
        return CompareJudgePayload.model_validate_json(stdout.strip()).to_verdicts(
            rubric_id
        )

    def invoke_baseline(self, prompt: str) -> ArtifactSet:
        with tempfile.TemporaryDirectory(prefix="eval-baseline-") as tmp:
            workdir = Path(tmp)
            self._chat_in_workdir(
                workdir,
                prompt,
                system=BASELINE_SYSTEM,
                provider_id=self._invoke_provider,
                model_id=self._invoke_model,
                operation="baseline",
                tools=_opencode_tools(),
            )
            return ArtifactSet(workdir=workdir, files=collect_text_artifacts(workdir))

    def classify(self, skill_description: str, query: str) -> bool:
        prompt = build_classify_prompt(skill_description, query)
        with tempfile.TemporaryDirectory(prefix="eval-classify-") as tmp:
            stdout = self._chat_in_workdir(
                Path(tmp),
                prompt,
                system=CLASSIFY_SYSTEM,
                provider_id=self._judge_provider,
                model_id=self._judge_model,
                operation="classify",
                tools=None,
            )
        return classify_token(stdout)

    def _chat_in_workdir(
        self,
        workdir: Path,
        prompt: str,
        system: str,
        provider_id: str,
        model_id: str,
        operation: str,
        tools: dict[str, bool] | None,
    ) -> str:
        port = _free_port()
        call = AdapterCall(
            adapter=_ADAPTER_NAME,
            operation=operation,
            provider=provider_id,
            model=model_id,
            prompt_chars=len(prompt),
            system_chars=len(system),
            timeout=self._timeout,
        )
        start = call.start()
        with _OpenCodeServer(self._opencode_path, workdir, port):
            client = cast(
                _OpenCodeClient,
                self._client_factory(f"http://{_HOSTNAME}:{port}", self._timeout),
            )
            session = client.session.create()
            try:
                message = client.session.chat(
                    session.id,
                    provider_id=provider_id,
                    model_id=model_id,
                    parts=[{"type": "text", "text": prompt}],
                    system=system,
                    tools=tools,
                    timeout=self._timeout,
                )
            except Exception as exc:
                raise call.abort(exc) from exc
            call.done(start)
            return _assistant_text(client.session.messages(session.id), message.id)

    def _load_skill_md(self, skill_name: str) -> str:
        path = self._skill_root / skill_name / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"SKILL.md not found for {skill_name!r} at {path}")
        return path.read_text(encoding="utf-8")

    def _stage_skill_resources(self, skill_name: str, workdir: Path) -> None:
        source = self._skill_root / skill_name
        shutil.copytree(
            source,
            workdir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("evals"),
        )


def _opencode_tools() -> dict[str, bool]:
    return dict.fromkeys(INVOKE_TOOLS, True)


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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
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
        return f"opencode serve exited {self._process.returncode} on port {self._port}"


def _create_client(base_url: str, timeout: int) -> _OpenCodeClient:
    return cast(
        _OpenCodeClient, Opencode(base_url=base_url, timeout=timeout, max_retries=0)
    )


def _assistant_text(messages: object, message_id: str | None) -> str:
    typed_messages = cast(list[_OpenCodeMessageWithParts], messages)
    if message_id is None:
        return _latest_assistant_text(typed_messages)
    for response_message in typed_messages:
        if response_message.info.id != message_id:
            continue
        return _message_text(response_message)
    raise RuntimeError(
        f"assistant message {message_id!r} not found in OpenCode session messages; "
        "expected message with text parts"
    )


def _latest_assistant_text(messages: list[_OpenCodeMessageWithParts]) -> str:
    for response_message in reversed(messages):
        role = getattr(response_message.info, "role", "assistant")
        if role != "assistant":
            continue
        text = _message_text(response_message)
        if text:
            return text
    raise RuntimeError(
        "assistant message id missing and no assistant text found in OpenCode "
        "session messages; expected a response with text parts"
    )


def _message_text(response_message: _OpenCodeMessageWithParts) -> str:
    text_parts = [
        part.text
        for part in response_message.parts
        if getattr(part, "type", None) == "text"
    ]
    return "\n".join(text_parts)


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
