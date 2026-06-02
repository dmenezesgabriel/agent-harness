"""Filesystem-layout conventions shared across the eval pipeline.

One home for the directory rules that the adapters, invoker, structural runner,
and judge would otherwise each restate: which path parts are never artifacts.
"""

from __future__ import annotations

from pathlib import Path

# Version-control and build directories that are never evaluation artifacts.
IGNORED_VCS_BUILD_PARTS = frozenset({".git", "dist", "node_modules"})


def has_ignored_part(relative_path: Path, extra: frozenset[str] = frozenset()) -> bool:
    """True when any path part is an ignored VCS/build dir or a caller-supplied extra.

    Artifact *collection* passes the staged skill-source names as `extra`; artifact
    *selection* ignores only the VCS/build base. Keeping the base in one place stops
    the two call sites from drifting.

    Usage:
        has_ignored_part(Path("node_modules/x/index.js"))  # True
        has_ignored_part(Path("SKILL.md"), frozenset({"SKILL.md"}))  # True
    """
    return bool((IGNORED_VCS_BUILD_PARTS | extra) & set(relative_path.parts))
