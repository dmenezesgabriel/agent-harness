"""Claude Code CLI adapter.

Invokes: claude --print "/<skill> <instruction>"  (slash command triggers skill)

Skills are project-level and must exist in the workspace under .agents/skills/<name>/.
This adapter copies the skill directory from the harness repo root into each temp
workspace before invoking the agent.

Token counts parsed from the stream-json result event (modelUsage for full session totals).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from harness.adapters.base import AgentAdapter
from harness.adapters.workspace import TempWorkspaceManager, WorkspaceManager
from harness.models import Task, TaskResult

_DEFAULT_MODEL = "claude-sonnet-4-6"
# Skills live at <repo_root>/.agents/skills/ — two levels up from benchmarks/harness/adapters/
_REPO_ROOT = Path(__file__).parents[3]
_SKILLS_SRC = _REPO_ROOT / ".agents" / "skills"


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude-code"

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_turns: int = 30,
        workspace_manager: WorkspaceManager = TempWorkspaceManager(),
    ):
        if not shutil.which("claude"):
            raise RuntimeError("claude CLI not found in PATH")
        self.model = model
        self.max_turns = max_turns
        self.workspace_manager = workspace_manager

    def _install_skill(self, skill: str, workspace: Path) -> None:
        """Copy skill files into .claude/skills/ so the slash command resolves.

        Claude Code discovers project skills from .claude/skills/<name>/SKILL.md.
        Skills in the harness repo use symlinks from .claude/skills/ → .agents/skills/,
        so we resolve the symlink (shutil.copytree with symlinks=False) when copying.
        """
        src = _SKILLS_SRC / skill
        if not src.is_dir():
            return
        dst = workspace / ".claude" / "skills" / skill
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, symlinks=False, dirs_exist_ok=True)

    def run(self, task: Task) -> TaskResult:
        instruction = task.instruction
        if task.codebase_context:
            instruction = f"{task.instruction}\n\n## Codebase Context\n\n{task.codebase_context}"

        prompt = f"/{task.skill} {instruction}"

        cmd = [
            "claude",
            "--output-format", "stream-json",
            "--verbose",
            "--permission-mode", "bypassPermissions",
            "--max-turns", str(self.max_turns),
            "--model", self.model,
            "--print",
            prompt,
        ]

        t0 = time.perf_counter()
        workspace = self.workspace_manager.init_workspace(task)
        try:
            self._install_skill(task.skill, workspace)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(workspace),
                timeout=300,
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            snapshot = self.workspace_manager.snapshot_workspace(workspace)

            return self._parse_stream(result.stdout, task, latency_ms, snapshot)
        except subprocess.TimeoutExpired:
            latency_ms = (time.perf_counter() - t0) * 1000
            return TaskResult(
                task_id=task.id, skill=task.skill, platform=self.name,
                raw_output="", latency_ms=latency_ms,
                input_tokens=0, output_tokens=0, error="timeout",
            )
        finally:
            self.workspace_manager.cleanup(workspace)

    def _parse_stream(
        self, stdout: str, task: Task,
        latency_ms: float,
        workspace_snapshot: dict[str, str] | None = None,
    ) -> TaskResult:
        text_parts: list[str] = []
        input_tokens = output_tokens = 0

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            etype = event.get("type", "")
            if etype == "assistant" and "message" in event:
                for block in event["message"].get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
            elif etype == "result":
                # modelUsage gives accurate totals across all turns including cache
                model_usage = event.get("modelUsage", {})
                if model_usage:
                    totals = next(iter(model_usage.values()), {})
                    input_tokens = totals.get("inputTokens", 0)
                    output_tokens = totals.get("outputTokens", 0)
                else:
                    usage = event.get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)

        return TaskResult(
            task_id=task.id,
            skill=task.skill,
            platform=self.name,
            raw_output="\n".join(text_parts),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            workspace_snapshot=workspace_snapshot or {},
        )
