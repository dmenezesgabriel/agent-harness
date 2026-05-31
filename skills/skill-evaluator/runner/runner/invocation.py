from __future__ import annotations

import shutil
from pathlib import Path

from runner.ports import AgentPort


class SkillInvoker:
    """Invoke a skill and persist produced artifacts for structural checks.

    Usage:
        live_dir = SkillInvoker().invoke('dataviz', Path('dataviz/evals'), adapter)
    """

    def invoke(self, skill_name: str, evals_dir: Path, adapter: AgentPort) -> Path:
        input_files = sorted((evals_dir / "fixtures").glob("input_*.md"))
        if not input_files:
            print(
                f"  No input_*.md fixtures found in {evals_dir / 'fixtures'} - skipping invocation"
            )
            return evals_dir / "fixtures"

        live_dir = evals_dir / "fixtures" / "_live"
        self._reset_live_dir(live_dir)

        input_text = input_files[0].read_text(encoding="utf-8")
        print(f"  Invoking skill with fixture: {input_files[0].name}")
        artifacts = adapter.invoke_skill(skill_name, input_text)
        self._write_artifacts(live_dir, artifacts.files)
        return live_dir

    def _reset_live_dir(self, live_dir: Path) -> None:
        if live_dir.exists():
            shutil.rmtree(live_dir)
        live_dir.mkdir(parents=True)
        (live_dir / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")

    def _write_artifacts(self, live_dir: Path, files: dict[str, str]) -> None:
        for rel_path, content in files.items():
            dest = live_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
