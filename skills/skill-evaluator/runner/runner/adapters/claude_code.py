"""ClaudeCodeAdapter — invokes skills and judges via the claude CLI.

Token counts are not available via the CLI; all eval results are based on
artifact files written to disk by the agent.

Skill invocation: haiku via --append-system-prompt-file (preserves tool defs).
Judge: sonnet via --system-prompt-file (replaces prompt, JSON-only output).
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
from contextlib import suppress
from pathlib import Path

from pydantic import BaseModel, Field

from runner.ports import ArtifactSet, JudgeVerdict

_DEFAULT_TIMEOUT_SECONDS = 180
_JUDGE_PASS_THRESHOLD = 0.7
_ERROR_PREVIEW_CHARS = 500
_INVOKE_MODEL = "haiku"
_JUDGE_MODEL = "sonnet"

_JUDGE_SYSTEM = (
    "You are an expert evaluator of AI-generated software artifacts. "
    "Respond ONLY with a JSON object — no prose, no markdown fences: "
    '{"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence>}'
)

_CLASSIFY_SYSTEM = (
    "You are an agent. You have access to one skill. "
    "When a user message matches the skill's purpose you invoke it; "
    "when it does not match you handle the request directly. "
    "Given the skill description and user message below, "
    "reply with exactly one word: INVOKE or SKIP. No explanation, no punctuation."
)

# Tools the skill is allowed to use when building artifacts
_INVOKE_TOOLS = "Write Read"


class _JudgePayload(BaseModel):
    passed: bool | None = None
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ClaudeCodeAdapter:
    """Run a skill or judge via `claude --print`.

    For skill invocation: runs in a temp workdir with Write/Read tool access
    so the model can create files. Collects those files as the artifact set.
    If the agent writes no files, the artifact set is empty and behave checks
    will fail — this is the correct signal, not something to paper over.

    Args:
        skill_root: Path to the skills/ directory.
        timeout: Seconds before the subprocess is killed.

    Usage:
        adapter = ClaudeCodeAdapter(skill_root=Path('skills'))
        artifacts = adapter.invoke_skill('dataviz', 'Make a line chart ...')
    """

    def __init__(
        self, skill_root: Path, timeout: int = _DEFAULT_TIMEOUT_SECONDS
    ) -> None:
        claude_path = shutil.which("claude")
        if not claude_path:
            raise RuntimeError(
                "claude CLI not found on PATH; install Claude Code first"
            )
        self._skill_root = skill_root
        self._timeout = timeout
        self._claude_path = claude_path

    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        skill_md = self._load_skill_md(skill_name)
        with tempfile.TemporaryDirectory(prefix=f"eval-{skill_name}-") as tmp:
            workdir = Path(tmp)
            self._run_in_dir(
                prompt,
                system=skill_md,
                model=_INVOKE_MODEL,
                workdir=workdir,
                tools=_INVOKE_TOOLS,
                append_system=True,
            )
            files = self._collect_dir(workdir)
            return ArtifactSet(workdir=workdir, files=files)

    def classify(self, skill_description: str, query: str) -> bool:
        prompt = f"Skill description:\n{skill_description}\n\nUser message:\n{query}"
        stdout = self._run_in_dir(
            prompt,
            system=_CLASSIFY_SYSTEM,
            model=_JUDGE_MODEL,
            workdir=None,
            tools=None,
            append_system=False,
        )
        token = stdout.strip().upper().split()[0] if stdout.strip() else ""
        return token == "INVOKE"

    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeVerdict:
        prompt = f"Rubric:\n{rubric}\n\nArtifact:\n{artifact_content}"
        stdout = self._run_in_dir(
            prompt,
            system=_JUDGE_SYSTEM,
            model=_JUDGE_MODEL,
            workdir=None,
            tools=None,
            append_system=False,
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

    def _run_in_dir(
        self,
        prompt: str,
        system: str,
        model: str,
        workdir: Path | None,
        tools: str | None,
        append_system: bool = False,
    ) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(system)
            system_file = f.name

        try:
            system_flag = (
                "--append-system-prompt-file"
                if append_system
                else "--system-prompt-file"
            )
            cmd = [
                self._claude_path,
                "--print",
                "--model",
                model,
                system_flag,
                system_file,
            ]
            if tools:
                cmd += ["--allowedTools", tools.replace(" ", ",")]

            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(workdir) if workdir else None,
                timeout=self._timeout,
                capture_output=True,
                text=True,
                check=False,
            )  # nosec B603
        finally:
            Path(system_file).unlink(missing_ok=True)

        if result.returncode != 0:
            raise RuntimeError(
                f"claude exited {result.returncode}\n"
                f"stderr: {result.stderr[:_ERROR_PREVIEW_CHARS]}\n"
                f"stdout: {result.stdout[:_ERROR_PREVIEW_CHARS]}"
            )
        return result.stdout

    def _collect_dir(self, workdir: Path) -> dict[str, str]:
        """Collect text files written by the model to workdir."""
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
