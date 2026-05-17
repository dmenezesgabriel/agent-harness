"""Compute a deterministic content hash over all files in a skill directory."""
from __future__ import annotations

import hashlib
from pathlib import Path


def compute_skill_hash(skill_dir: Path) -> str:
    """sha256 over sorted <relative_path>:<file_content> for every file in skill_dir.

    Returns the first 16 hex chars prefixed with 'sha256:'.
    """
    h = hashlib.sha256()
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(skill_dir))
        h.update(rel.encode())
        h.update(b":")
        h.update(p.read_bytes())
    return f"sha256:{h.hexdigest()[:16]}"
