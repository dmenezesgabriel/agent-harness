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
from pathlib import Path

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
from runner.metrics import CallMetricsCollector
from runner.models import JudgeReport
from runner.ports import ArtifactSet

_DEFAULT_TIMEOUT_SECONDS = 180
_ADAPTER_NAME = "ClaudeCode"
_PROVIDER_NAME = "claude-cli"
_ERROR_PREVIEW_CHARS = 500
_INVOKE_MODEL = "haiku"
_JUDGE_MODEL = "sonnet"
_CLASSIFY_MODEL = "haiku"


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
        self,
        skill_root: Path,
        timeout: int = _DEFAULT_TIMEOUT_SECONDS,
        collector: CallMetricsCollector | None = None,
    ) -> None:
        claude_path = shutil.which("claude")
        if not claude_path:
            raise RuntimeError(
                "claude CLI not found on PATH; install Claude Code first"
            )
        self._skill_root = skill_root
        self._timeout = timeout
        self._claude_path = claude_path
        self._collector = collector

    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        skill_md = self._load_skill_md(skill_name)
        with tempfile.TemporaryDirectory(prefix=f"eval-{skill_name}-") as tmp:
            workdir = Path(tmp)
            self._stage_skill_resources(skill_name, workdir)
            self._run_in_dir(
                prompt,
                system=skill_md,
                model=_INVOKE_MODEL,
                workdir=workdir,
                tools=_claude_tools(),
                operation=f"invoke:{skill_name}",
                append_system=True,
            )
            return ArtifactSet(workdir=workdir, files=collect_text_artifacts(workdir))

    def invoke_baseline(self, prompt: str) -> ArtifactSet:
        with tempfile.TemporaryDirectory(prefix="eval-baseline-") as tmp:
            workdir = Path(tmp)
            self._run_in_dir(
                prompt,
                system=BASELINE_SYSTEM,
                model=_INVOKE_MODEL,
                workdir=workdir,
                tools=_claude_tools(),
                operation="baseline",
                append_system=False,
            )
            return ArtifactSet(workdir=workdir, files=collect_text_artifacts(workdir))

    def classify(self, skill_description: str, query: str) -> bool:
        prompt = build_classify_prompt(skill_description, query)
        stdout = self._run_in_dir(
            prompt,
            system=CLASSIFY_SYSTEM,
            model=_CLASSIFY_MODEL,
            workdir=None,
            tools=None,
            operation="classify",
            append_system=False,
        )
        return classify_token(stdout)

    def judge(self, artifact_content: str, rubric: str, rubric_id: str) -> JudgeReport:
        prompt = build_judge_prompt(artifact_content, rubric)
        stdout = self._run_in_dir(
            prompt,
            system=JUDGE_SYSTEM,
            model=_JUDGE_MODEL,
            workdir=None,
            tools=None,
            operation=f"judge:{rubric_id}",
            append_system=False,
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
        stdout = self._run_in_dir(
            prompt,
            system=COMPARE_JUDGE_SYSTEM,
            model=_JUDGE_MODEL,
            workdir=None,
            tools=None,
            operation=f"compare_judge:{rubric_id}",
            append_system=False,
        )
        return CompareJudgePayload.model_validate_json(stdout.strip()).to_verdicts(
            rubric_id
        )

    def _run_in_dir(
        self,
        prompt: str,
        system: str,
        model: str,
        workdir: Path | None,
        tools: str | None,
        operation: str,
        append_system: bool = False,
    ) -> str:
        call = AdapterCall(
            adapter=_ADAPTER_NAME,
            operation=operation,
            provider=_PROVIDER_NAME,
            model=model,
            prompt_chars=len(prompt),
            system_chars=len(system),
            timeout=self._timeout,
            collector=self._collector,
        )
        start = call.start()
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

            try:
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    cwd=str(workdir) if workdir else None,
                    timeout=self._timeout,
                    capture_output=True,
                    text=True,
                    check=False,
                )  # nosec B603
            except subprocess.TimeoutExpired as exc:
                raise call.abort(exc) from exc
        finally:
            Path(system_file).unlink(missing_ok=True)

        if result.returncode != 0:
            raise call.abort(_subprocess_error(result))
        call.done(start)
        return result.stdout

    def _stage_skill_resources(self, skill_name: str, workdir: Path) -> None:
        source = self._skill_root / skill_name
        shutil.copytree(
            source,
            workdir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("evals"),
        )

    def _load_skill_md(self, skill_name: str) -> str:
        path = self._skill_root / skill_name / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"SKILL.md not found for {skill_name!r} at {path}")
        return path.read_text(encoding="utf-8")


def _claude_tools() -> str:
    return ",".join(tool.title() for tool in INVOKE_TOOLS)


def _subprocess_error(result: subprocess.CompletedProcess[str]) -> RuntimeError:
    return RuntimeError(
        f"claude exited {result.returncode}\n"
        f"stderr: {result.stderr[:_ERROR_PREVIEW_CHARS]}\n"
        f"stdout: {result.stdout[:_ERROR_PREVIEW_CHARS]}"
    )
