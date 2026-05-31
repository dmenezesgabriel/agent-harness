from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class ArtifactSet(BaseModel):
    """Files produced by one skill invocation.

    files maps relative paths (e.g. 'tasks/issues/001-foo.md') to contents.

    Usage:
        artifacts = ArtifactSet(workdir=Path('/tmp/run'))
        content = artifacts.get('tasks/issues/001-foo.md')
        issues = artifacts.matching('tasks/issues/*.md')
    """

    workdir: Path
    files: dict[str, str] = Field(default_factory=dict)

    def get(self, relative_path: str) -> str | None:
        return self.files.get(relative_path)

    def matching(self, glob: str) -> dict[str, str]:
        return {k: v for k, v in self.files.items() if Path(k).match(glob)}


class JudgeVerdict(BaseModel):
    rubric_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class AgentPort(Protocol):
    """Invoke a skill against a prompt and return the produced artifacts.

    Usage:
        adapter = ClaudeCodeAdapter(skill_root=Path('skills'))
        artifacts = adapter.invoke_skill('plan-it', 'Add login feature')
    """

    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet: ...


class JudgePort(Protocol):
    """Evaluate artifact content against a rubric string, return a verdict.

    Usage:
        verdict = judge.judge(artifact_content, rubric_text, rubric_id='context_relevance')
    """

    def judge(
        self, artifact_content: str, rubric: str, rubric_id: str
    ) -> JudgeVerdict: ...
