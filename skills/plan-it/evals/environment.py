import os
from pathlib import Path
from typing import Protocol


class ArtifactContext(Protocol):
    artifacts: dict[str, str]
    fixture_name: str


def before_scenario(context: ArtifactContext, _scenario: object) -> None:
    base = os.environ.get("EVAL_ARTIFACTS_DIR")
    artifacts_dir = (
        Path(base) if base else Path(__file__).parent / "fixtures" / "golden"
    )
    context.fixture_name = artifacts_dir.name
    context.artifacts = {
        str(path.relative_to(artifacts_dir)): path.read_text(encoding="utf-8")
        for path in artifacts_dir.rglob("*")
        if path.is_file()
        and "dist" not in path.relative_to(artifacts_dir).parts
        and "node_modules" not in path.relative_to(artifacts_dir).parts
    }
