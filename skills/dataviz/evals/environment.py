import os
from pathlib import Path
from typing import Protocol


class ArtifactContext(Protocol):
    artifacts: dict[str, str]


def before_scenario(context: ArtifactContext, _scenario: object) -> None:
    base = os.environ.get("EVAL_ARTIFACTS_DIR")
    fixtures_dir = Path(base) if base else Path(__file__).parent / "fixtures"
    context.artifacts = {
        str(p.relative_to(fixtures_dir)): p.read_text(encoding="utf-8")
        for p in fixtures_dir.rglob("*")
        if p.is_file()
        and not p.name.startswith("input_")
        and "_live" not in p.relative_to(fixtures_dir).parts
    }
