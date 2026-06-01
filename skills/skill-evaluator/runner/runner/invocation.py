from __future__ import annotations

import shutil
from pathlib import Path

from runner.ports import AgentPort, BaselineAgentPort


class SkillInvoker:
    """Invoke a skill and persist produced artifacts for structural checks.

    Usage:
        live_dir = SkillInvoker().invoke('dataviz', Path('dataviz/evals'), adapter)
    """

    def invoke(self, skill_name: str, evals_dir: Path, adapter: AgentPort) -> Path:
        input_files = sorted((evals_dir / "fixtures" / "inputs").glob("*.md"))
        if not input_files:
            print(
                f"  No input prompts found in {evals_dir / 'fixtures' / 'inputs'} - skipping invocation"
            )
            return evals_dir / "fixtures" / "golden"

        generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
        self._reset_generated_artifacts_dir(generated_dir)

        input_text = input_files[0].read_text(encoding="utf-8")
        print(f"  Invoking skill with fixture: {input_files[0].name}")
        artifacts = adapter.invoke_skill(skill_name, input_text)
        self._write_artifacts(generated_dir, artifacts.files)
        return generated_dir

    def invoke_baseline(self, evals_dir: Path, agent: BaselineAgentPort) -> Path:
        input_files = sorted((evals_dir / "fixtures" / "inputs").glob("*.md"))
        if not input_files:
            print(
                f"  No input prompts found in {evals_dir / 'fixtures' / 'inputs'} - skipping baseline"
            )
            return evals_dir / "fixtures" / "golden"

        baseline_dir = evals_dir / "fixtures" / "_baseline_artifacts"
        self._reset_generated_artifacts_dir(baseline_dir)

        input_text = input_files[0].read_text(encoding="utf-8")
        print(f"  Invoking baseline with fixture: {input_files[0].name}")
        artifacts = agent.invoke_baseline(input_text)
        self._write_artifacts(baseline_dir, artifacts.files)
        return baseline_dir

    def _reset_generated_artifacts_dir(self, generated_dir: Path) -> None:
        if generated_dir.exists():
            shutil.rmtree(generated_dir)
        generated_dir.mkdir(parents=True)
        (generated_dir / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")

    def _write_artifacts(self, generated_dir: Path, files: dict[str, str]) -> None:
        for rel_path, content in files.items():
            dest = generated_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
