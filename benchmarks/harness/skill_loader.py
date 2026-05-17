"""Assembles a skill's full system prompt from SKILL.md and its references."""
from __future__ import annotations

import re
from pathlib import Path


_SKILLS_ROOT = Path(__file__).parent.parent.parent / "skills"


def _resolve_reference_link(text: str, skill_dir: Path) -> str:
    """Inline referenced markdown files that appear as [name](references/foo.md) links."""
    def replace_link(m: re.Match) -> str:
        link_path = skill_dir / m.group(2)
        if link_path.exists() and link_path.suffix == ".md":
            content = link_path.read_text()
            return f"\n\n---\n## Referenced: {link_path.name}\n\n{content}\n\n---\n"
        return m.group(0)

    return re.sub(r"\[([^\]]+)\]\((references/[^)]+\.md)[^)]*\)", replace_link, text)


def load_skill_prompt(skill_name: str) -> str:
    """Return the full system prompt for a skill (SKILL.md + all referenced files)."""
    skill_dir = _SKILLS_ROOT / skill_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"Skill not found: {skill_dir}")

    content = skill_md.read_text()
    content = _resolve_reference_link(content, skill_dir)

    # also load any assets referenced
    assets_dir = skill_dir / "assets"
    if assets_dir.exists():
        for asset in sorted(assets_dir.glob("*.md")):
            content += f"\n\n---\n## Asset: {asset.name}\n\n{asset.read_text()}\n\n---\n"

    return content


def baseline_prompt() -> str:
    return (
        "You are a senior software engineer assistant. "
        "Help the user with software engineering tasks including planning, "
        "implementation, code review, and architecture. "
        "Be practical, precise, and concise."
    )
