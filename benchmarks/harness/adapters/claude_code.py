"""Claude Code CLI adapter.

With skill:    claude --print "/plan-it <instruction>"  (slash command triggers skill)
Without skill: claude --print "<instruction>"           (no skill, raw Claude behavior)

Skill variants: since Claude Code resolves skills by name from the skills/ directory,
swap the SKILL.md file before running. Pass skill_dir to use a modified skill copy.

Token counts parsed from the stream-json result event.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from harness.adapters._workspace import init_workspace, snapshot_workspace
from harness.adapters.base import AgentAdapter
from harness.models import Condition, Task, TrialResult

_DEFAULT_MODEL = "claude-sonnet-4-6"


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude-code"

    def __init__(self, model: str = _DEFAULT_MODEL, max_turns: int = 10):
        if not shutil.which("claude"):
            raise RuntimeError("claude CLI not found in PATH")
        self.model = model
        self.max_turns = max_turns

    def run(self, task: Task, condition: Condition, trial_index: int) -> TrialResult:
        instruction = task.instruction
        if task.codebase_context:
            instruction = f"{task.instruction}\n\n## Codebase Context\n\n{task.codebase_context}"

        if condition == Condition.WITH_SKILL:
            # slash command triggers the skill's SKILL.md as system context
            prompt = f"/{task.skill} {instruction}"
        else:
            prompt = instruction

        cmd = [
            "claude",
            "--output-format", "stream-json",
            "--max-turns", str(self.max_turns),
            "--model", self.model,
            "--print",
            prompt,
        ]

        t0 = time.perf_counter()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                workspace = Path(tmp)
                init_workspace(workspace)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(workspace),
                    timeout=300,
                )
                latency_ms = (time.perf_counter() - t0) * 1000
                snapshot = snapshot_workspace(workspace)

            return self._parse_stream(
                result.stdout, task, condition, trial_index, latency_ms, snapshot
            )
        except subprocess.TimeoutExpired:
            latency_ms = (time.perf_counter() - t0) * 1000
            return TrialResult(
                task_id=task.id, skill=task.skill, platform=self.name,
                condition=condition.value, trial_index=trial_index,
                raw_output="", latency_ms=latency_ms,
                input_tokens=0, output_tokens=0, error="timeout",
            )

    def _parse_stream(
        self, stdout: str, task: Task, condition: Condition,
        trial_index: int, latency_ms: float,
        workspace_snapshot: dict[str, str] | None = None,
    ) -> TrialResult:
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
                usage = event.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

        return TrialResult(
            task_id=task.id,
            skill=task.skill,
            platform=self.name,
            condition=condition.value,
            trial_index=trial_index,
            raw_output="\n".join(text_parts),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            workspace_snapshot=workspace_snapshot or {},
        )
