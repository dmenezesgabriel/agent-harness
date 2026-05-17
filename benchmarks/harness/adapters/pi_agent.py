"""Pi coding agent adapter.

With skill:    pi --print --model <m> --skill <skills/plan-it> "<instruction>"
Without skill: pi --print --model <m> --no-skills "<instruction>"

Workspace: pi runs in a fresh temp directory per trial. For file-writing skills
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
import tempfile
import time
from pathlib import Path

import tiktoken

from harness.adapters._workspace import init_workspace, snapshot_workspace
from harness.adapters.base import AgentAdapter
from harness.models import Condition, Task, TrialResult

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_MODEL = "openai-codex/gpt-5.4-mini"
_ENC = tiktoken.get_encoding("cl100k_base")

# output directories the skill expects to exist (pre-created so script confusion is irrelevant)
_OUTPUT_DIRS = ["issues", "implementation", "docs/adrs"]

# after the run, collect written files from these subdirs (skill output artifacts)
_OUTPUT_GLOBS = ["issues/**/*.md", "implementation/**/*.md", "docs/adrs/**/*.md"]


def _approx_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def _collect_workspace_output(workspace: Path) -> str:
    """Concatenate all skill-output files for text evaluation."""
    parts: list[str] = []
    for pattern in _OUTPUT_GLOBS:
        for p in sorted(workspace.glob(pattern)):
            parts.append(f"<!-- file: {p.relative_to(workspace)} -->\n{p.read_text()}")
    return "\n\n".join(parts)



class PiAgentAdapter(AgentAdapter):
    name = "pi-agent"

    def __init__(self, model: str = _DEFAULT_MODEL, skill_dir: str | None = None):
        if not shutil.which("pi"):
            raise RuntimeError("pi CLI not found in PATH")
        self.model = model
        self._skill_dir = Path(skill_dir) if skill_dir else None

    def run(self, task: Task, condition: Condition, trial_index: int) -> TrialResult:
        prompt = task.instruction
        if task.codebase_context:
            prompt = f"{task.instruction}\n\n## Codebase Context\n\n{task.codebase_context}"

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            # initialise an isolated git root with pre-created output dirs so the
            # skill can write files without walking up to the real repo
            init_workspace(workspace)

            # copy the skill's own scripts/ into workspace/scripts/ first,
            # then overlay repo scripts/ — skill-specific scripts take precedence
            # because SKILL.md was written against them
            if condition == Condition.WITH_SKILL:
                skill_path = self._skill_dir or (_REPO_ROOT / "skills" / task.skill)
                skill_scripts = skill_path / "scripts"
                if skill_scripts.exists():
                    shutil.copytree(skill_scripts, workspace / "scripts")

            cmd = ["pi", "--print", "--model", self.model, "--no-session"]

            if condition == Condition.WITH_SKILL:
                cmd += ["--skill", str(skill_path)]
            else:
                cmd += ["--no-skills"]

            cmd.append(prompt)

            t0 = time.perf_counter()
            try:
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
                snapshot = snapshot_workspace(workspace)

                return TrialResult(
                    task_id=task.id,
                    skill=task.skill,
                    platform=self.name,
                    condition=condition.value,
                    trial_index=trial_index,
                    raw_output=raw_output,
                    latency_ms=latency_ms,
                    input_tokens=_approx_tokens(prompt),
                    output_tokens=_approx_tokens(raw_output),
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
                return TrialResult(
                    task_id=task.id, skill=task.skill, platform=self.name,
                    condition=condition.value, trial_index=trial_index,
                    raw_output="", latency_ms=latency_ms,
                    input_tokens=0, output_tokens=0, error="timeout",
                )
