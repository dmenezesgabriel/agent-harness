"""Zero-token pre-flight validator for skill directories.

Checks SKILL.md presence and resolves all [label](references/...) and
[label](assets/...) links before any adapter is invoked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LintError:
    path: str
    message: str


@dataclass
class LintResult:
    skill: str
    errors: list[LintError] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


_LINK_RE = re.compile(r"\[([^\]]+)\]\(((references|assets)/[^)]+)\)")


class SkillLintValidator:
    def validate(self, skill_dir: Path) -> LintResult:
        result = LintResult(skill=skill_dir.name)

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            result.errors.append(LintError(
                path="SKILL.md",
                message=f"SKILL.md not found in {skill_dir}",
            ))
            return result

        content = skill_md.read_text()
        for match in _LINK_RE.finditer(content):
            link_path = match.group(2).split("#")[0]
            if not (skill_dir / link_path).exists():
                result.errors.append(LintError(
                    path=link_path,
                    message=f"Linked file not found: {link_path}",
                ))

        return result
