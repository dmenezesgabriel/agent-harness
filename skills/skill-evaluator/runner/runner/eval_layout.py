"""Filesystem-layout conventions shared across the eval pipeline.

One home for the directory rules that the adapters, invoker, structural runner,
and judge would otherwise each restate: which path parts are never artifacts.
"""

from __future__ import annotations

from pathlib import Path

# Version-control and build directories that are never evaluation artifacts.
IGNORED_VCS_BUILD_PARTS = frozenset({".git", "dist", "node_modules"})

# Prefix marking a per-fixture artifact subdirectory. The invoker writes these and
# the structural runner detects them; sharing the prefix keeps the two in lockstep
# instead of relying on input fixtures happening to be named "input_*".
INPUT_FIXTURE_DIR_PREFIX = "input_"


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


def fixture_input_files(evals_dir: Path, limit: int) -> list[Path]:
    """The first `limit` sorted input-prompt fixtures for a skill's eval dir.

    Single definition of "which input fixtures a run invokes" so the invoker and
    the input-size reporter always agree on the set.

    Usage:
        fixture_input_files(Path("skills/dataviz/evals"), 2)
    """
    inputs = sorted((evals_dir / "fixtures" / "inputs").glob("*.md"))
    return inputs[:limit]


def fixture_artifact_dir(base: Path, input_file: Path) -> Path:
    """Per-fixture artifact subdir whose name always carries INPUT_FIXTURE_DIR_PREFIX.

    Guarantees the prefix even when the fixture stem lacks it, so is_input_artifact_dir
    can detect the subdir regardless of how the fixture file was named.

    Usage:
        fixture_artifact_dir(Path("out"), Path("inputs/basic.md"))  # out/input_basic
    """
    stem = input_file.stem
    name = (
        stem
        if stem.startswith(INPUT_FIXTURE_DIR_PREFIX)
        else f"{INPUT_FIXTURE_DIR_PREFIX}{stem}"
    )
    return base / name


def is_input_artifact_dir(path: Path) -> bool:
    """True for a per-fixture artifact subdir produced by fixture_artifact_dir.

    Usage:
        is_input_artifact_dir(Path("out/input_basic"))  # True
    """
    return path.is_dir() and path.name.startswith(INPUT_FIXTURE_DIR_PREFIX)
