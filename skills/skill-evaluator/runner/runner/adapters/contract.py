from __future__ import annotations

import time
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import structlog

from runner.exceptions import ProviderAbortError

_log = structlog.get_logger()

JUDGE_SYSTEM = (
    "You are an expert evaluator of AI-generated software artifacts. "
    "Fail superficial compliance: correct structure but empty or placeholder content. "
    "Respond ONLY with a JSON object - no prose, no markdown fences: "
    '{"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence citing artifact evidence>}'
)

COMPARE_JUDGE_SYSTEM = (
    "You are an expert evaluator of AI-generated software artifacts. "
    "You receive two artifacts - Skill (produced with skill guidance) and Baseline "
    "(produced without guidance) - and a rubric. Evaluate each independently. "
    "Respond ONLY with a JSON object - no prose, no markdown fences: "
    '{"skill": {"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence citing artifact evidence>}, '
    '"baseline": {"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence citing artifact evidence>}}'
)

CLASSIFY_SYSTEM = (
    "You are an agent. You have access to one skill. "
    "When a user message matches the skill's purpose you invoke it; "
    "when it does not match you handle the request directly. "
    "Given the skill description and user message below, "
    "reply with exactly one word: INVOKE or SKIP. No explanation, no punctuation."
)

BASELINE_SYSTEM = "You are a helpful assistant. Complete the task the user describes."

INVOKE_TOOLS = ("bash", "read", "write")

IGNORED_ARTIFACT_PARTS = frozenset(
    {".git", "dist", "node_modules", "SKILL.md", "assets", "references", "scripts"}
)


class ProviderFailureReason(StrEnum):
    RATE_LIMIT = "rate limit"
    TIMEOUT = "timeout"
    PROVIDER_FAILURE = "provider failure"


@dataclass(frozen=True)
class AdapterCall:
    adapter: str
    operation: str
    provider: str
    model: str
    prompt_chars: int
    system_chars: int
    timeout: int

    def start(self) -> float:
        _log.info("adapter_call_start", **self._fields())
        return time.monotonic()

    def done(self, started_at: float) -> None:
        _log.info(
            "adapter_call_done",
            elapsed_s=round(time.monotonic() - started_at, 1),
            **self._fields(),
        )

    def abort(self, exc: Exception) -> ProviderAbortError:
        reason = provider_failure_reason(exc)
        _log.error("adapter_call_aborted", reason=reason, error=repr(exc), **self._fields())
        return ProviderAbortError(self.abort_message(reason, exc))

    def abort_message(self, reason: ProviderFailureReason, exc: Exception) -> str:
        return (
            f"{self.adapter} {reason} during {self.operation}; "
            f"provider={self.provider!r}, model={self.model!r}, "
            f"timeout_s={self.timeout}, error={exc!r}"
        )

    def _fields(self) -> dict[str, object]:
        return {
            "adapter": self.adapter,
            "operation": self.operation,
            "provider": self.provider,
            "model": self.model,
            "prompt_chars": self.prompt_chars,
            "system_chars": self.system_chars,
            "timeout_s": self.timeout,
        }


def build_classify_prompt(skill_description: str, query: str) -> str:
    return f"Skill description:\n{skill_description}\n\nUser message:\n{query}"


def build_judge_prompt(artifact_content: str, rubric: str) -> str:
    return f"Rubric:\n{rubric}\n\nArtifact:\n{artifact_content}"


def build_compare_judge_prompt(
    skill_content: str, baseline_content: str, rubric: str
) -> str:
    return (
        f"Rubric:\n{rubric}\n\n"
        f"Artifact (Skill):\n{skill_content}\n\n"
        f"Artifact (Baseline):\n{baseline_content}"
    )


def classify_token(stdout: str) -> bool:
    token = stdout.strip().upper().split()[0] if stdout.strip() else ""
    return token == "INVOKE"  # nosec B105


def collect_text_artifacts(workdir: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in workdir.rglob("*"):
        _collect_text_file(workdir, path, files)
    return files


def provider_failure_reason(exc: Exception) -> ProviderFailureReason:
    text = f"{type(exc).__name__} {exc}".lower()
    if "rate limit" in text or "429" in text or "quota" in text:
        return ProviderFailureReason.RATE_LIMIT
    if "timeout" in text or "timed out" in text:
        return ProviderFailureReason.TIMEOUT
    return ProviderFailureReason.PROVIDER_FAILURE


def _collect_text_file(workdir: Path, path: Path, files: dict[str, str]) -> None:
    if not path.is_file() or _has_ignored_part(path.relative_to(workdir)):
        return
    with suppress(UnicodeDecodeError):
        files[str(path.relative_to(workdir))] = path.read_text(encoding="utf-8")


def _has_ignored_part(relative_path: Path) -> bool:
    return bool(IGNORED_ARTIFACT_PARTS & set(relative_path.parts))
