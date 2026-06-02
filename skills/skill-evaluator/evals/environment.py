import os
from pathlib import Path
from typing import Protocol


class ArtifactContext(Protocol):
    artifacts: dict[str, str]


def before_scenario(context: ArtifactContext, _scenario: object) -> None:
    base = os.environ.get("EVAL_ARTIFACTS_DIR")
    artifacts_dir = (
        Path(base) if base else Path(__file__).parent / "fixtures" / "golden"
    )
    context.artifacts = {
        str(path.relative_to(artifacts_dir)): path.read_text(encoding="utf-8")
        for path in artifacts_dir.rglob("*")
        if path.is_file()
    }
