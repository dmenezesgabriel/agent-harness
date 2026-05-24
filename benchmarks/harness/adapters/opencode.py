"""OpenCode adapter.

Runs from a temp workspace that contains a copy of opencode.json and the
skills/ directory. opencode auto-loads skills from opencode.json skills.paths,
which resolve relative to its location.

The --dir flag tells opencode where to write files (the isolated workspace),
regardless of which directory is detected as the project root.

Token counts: parsed from step_finish events in --format json output.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from harness.adapters.base import AgentAdapter
from harness.adapters.workspace import TempWorkspaceManager, WorkspaceManager, diff_workspace
from harness.models import Task, TaskResult

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_MODEL = "opencode/big-pickle"


class OpenCodeAdapter(AgentAdapter):
    name = "opencode"

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        workspace_manager: WorkspaceManager = TempWorkspaceManager(),
    ):
        if not shutil.which("opencode"):
            raise RuntimeError(
                "opencode CLI not found in PATH. "
                "Install: npm i -g opencode-ai  or  pnpm add -g opencode-ai"
            )
        self.model = model
        self.workspace_manager = workspace_manager

    def run(self, task: Task) -> TaskResult:
        prompt = task.instruction
        if task.codebase_context:
            prompt = f"{task.instruction}\n\n## Codebase Context\n\n{task.codebase_context}"

        t0 = time.perf_counter()
        workspace = self.workspace_manager.init_workspace(task)
        try:
            # Copy opencode.json so opencode resolves skills.paths from
            # the workspace. Then copy skills/ so those relative paths exist.
            src_config = _REPO_ROOT / "opencode.json"
            if src_config.exists():
                shutil.copy2(src_config, workspace / "opencode.json")
            src_skills = _REPO_ROOT / "skills"
            if src_skills.exists():
                shutil.copytree(src_skills, workspace / "skills")
            before_snapshot = self.workspace_manager.snapshot_workspace(workspace)

            cmd = [
                "opencode", "run",
                "--model", self.model,
                "--format", "json",
                "--dir", str(workspace),
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
            after_snapshot = self.workspace_manager.snapshot_workspace(workspace)
            snapshot = diff_workspace(before_snapshot, after_snapshot)
            filtered_count = len(after_snapshot) - len(snapshot)

            task_result = self._parse_output(
                result.stdout, task, latency_ms, snapshot
            )
            if filtered_count:
                task_result.evaluator_details["scaffold_files_filtered"] = filtered_count
            return task_result
        except subprocess.TimeoutExpired:
            latency_ms = (time.perf_counter() - t0) * 1000
            return TaskResult(
                task_id=task.id, skill=task.skill, platform=self.name,
                raw_output="", latency_ms=latency_ms,
                input_tokens=0, output_tokens=0, error="timeout",
            )
        finally:
            self.workspace_manager.cleanup(workspace)

    def _parse_output(
        self,
        stdout: str,
        task: Task,
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
                text_parts.append(line)
                continue

            etype = event.get("type", "")
            if etype == "text":
                # opencode text events: {"type":"text","part":{"text":"..."}}
                text_parts.append(event.get("part", {}).get("text", ""))
            elif etype == "step_finish":
                tokens = event.get("part", {}).get("tokens", {})
                if "input" in tokens:
                    input_tokens += tokens["input"]
                if "output" in tokens:
                    output_tokens += tokens["output"]

        raw = "\n".join(p for p in text_parts if p).strip() or stdout.strip()
        return TaskResult(
            task_id=task.id,
            skill=task.skill,
            platform=self.name,
            raw_output=raw,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            workspace_snapshot=workspace_snapshot or {},
        )
