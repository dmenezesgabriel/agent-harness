"""Pi coding agent adapter.

Invokes: pi --print --model <m> --skill <skills/plan-it> "<instruction>"

Workspace: pi runs in a fresh temp directory per task. For file-writing skills
(plan-it, implement-it) the temp dir includes the repo's scripts/ so the skill
can call ensure-issues-dir.sh etc. After pi exits, any files written to the
workspace are collected and used as the primary output for evaluation.

Token counts: pi loads skill files internally so we can't measure input tokens
including the skill system prompt. We approximate using tiktoken and tag runs
with approx_tokens=true.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import tiktoken

from harness.adapters.base import AgentAdapter
from harness.adapters.workspace import TempWorkspaceManager, WorkspaceManager
from harness.models import Task, TaskResult

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_MODEL = "openai-codex/gpt-5.4-mini"
_ENC = tiktoken.get_encoding("cl100k_base")

# output directories the skill expects to exist (pre-created so script confusion is irrelevant)
_OUTPUT_DIRS = ["issues", "implementation", "docs/adrs"]

# after the run, collect written files from these subdirs (skill output artifacts)
_OUTPUT_GLOBS = ["issues/**/*.md", "implementation/**/*.md", "docs/adrs/**/*.md"]


def _approx_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def _skill_prompt_tokens(skill_path: Path) -> int:
    """Count tokens the skill system prompt adds: SKILL.md + references/*.md + assets/*.md."""
    total = 0
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        total += _approx_tokens(skill_md.read_text())
    for subdir in ("references", "assets"):
        d = skill_path / subdir
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                total += _approx_tokens(f.read_text())
    return total


def _collect_workspace_output(workspace: Path) -> str:
    """Concatenate all skill-output files for text evaluation."""
    parts: list[str] = []
    for pattern in _OUTPUT_GLOBS:
        for p in sorted(workspace.glob(pattern)):
            parts.append(f"<!-- file: {p.relative_to(workspace)} -->\n{p.read_text()}")
    return "\n\n".join(parts)



class PiAgentAdapter(AgentAdapter):
    name = "pi-agent"

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        skill_dir: str | None = None,
        workspace_manager: WorkspaceManager = TempWorkspaceManager(),
    ):
        if not shutil.which("pi"):
            raise RuntimeError("pi CLI not found in PATH")
        self.model = model
        self._skill_dir = Path(skill_dir) if skill_dir else None
        self.workspace_manager = workspace_manager

    def run(self, task: Task) -> TaskResult:
        prompt = task.instruction
        if task.codebase_context:
            prompt = f"{task.instruction}\n\n## Codebase Context\n\n{task.codebase_context}"

        workspace: Path | None = None
        t0 = time.perf_counter()
        try:
            workspace = self.workspace_manager.init_workspace(task)

            skill_path = self._skill_dir or (_REPO_ROOT / "skills" / task.skill)
            skill_scripts = skill_path / "scripts"
            if skill_scripts.exists():
                shutil.copytree(skill_scripts, workspace / "scripts")

            cmd = [
                "pi", "--print", "--model", self.model, "--no-session",
                "--skill", str(skill_path),
                prompt,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(workspace),
                timeout=300,
            )
            latency_ms = (time.perf_counter() - t0) * 1000

            stdout = result.stdout.strip()
            error = f"exit {result.returncode}" if result.returncode != 0 else ""

            workspace_output = _collect_workspace_output(workspace)
            raw_output = workspace_output if workspace_output else stdout
            snapshot = self.workspace_manager.snapshot_workspace(workspace)

            input_tokens = _approx_tokens(prompt) + _skill_prompt_tokens(skill_path)

            if snapshot:
                output_tokens = sum(_approx_tokens(v) for v in snapshot.values())
            else:
                output_tokens = _approx_tokens(raw_output)

            return TaskResult(
                task_id=task.id,
                skill=task.skill,
                platform=self.name,
                raw_output=raw_output,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                workspace_snapshot=snapshot,
                error=error,
                evaluator_details={
                    "approx_tokens": True,
                    "wrote_files": bool(workspace_output),
                    "stdout_len": len(stdout),
                },
            )
        except subprocess.TimeoutExpired:
            latency_ms = (time.perf_counter() - t0) * 1000
            return TaskResult(
                task_id=task.id, skill=task.skill, platform=self.name,
                raw_output="", latency_ms=latency_ms,
                input_tokens=0, output_tokens=0, error="timeout",
            )
        finally:
            if workspace is not None:
                self.workspace_manager.cleanup(workspace)
