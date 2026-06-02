from __future__ import annotations

from pathlib import Path


class SkillDiscovery:
    """Discover skill eval directories under the skills root.

    Usage:
        discovery = SkillDiscovery(Path('skills'))
        eval_dirs = discovery.discover('plan-it')
    """

    def __init__(self, skills_root: Path) -> None:
        self._skills_root = skills_root

    def discover(self, skill_filter: str | None) -> list[Path]:
        dirs: list[Path] = []
        for evals_dir in sorted(self._skills_root.glob("*/evals")):
            if self._should_include(evals_dir, skill_filter):
                dirs.append(evals_dir)
        return dirs

    @property
    def skills_root(self) -> Path:
        return self._skills_root

    def _should_include(self, evals_dir: Path, skill_filter: str | None) -> bool:
        if not evals_dir.is_dir():
            return False
        if evals_dir.parent.name == "skill-evaluator" and skill_filter is None:
            return False
        return skill_filter is None or evals_dir.parent.name == skill_filter
