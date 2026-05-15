# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_KEYS = ["id", "skill_targets", "category", "fixture", "prompt", "success_criteria", "artifacts", "run", "checks"]


def validate_task(task_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(task_path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{task_path}: invalid JSON: {exc}"]
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"{task_path}: missing key '{key}'")
    fixture = Path(data.get("fixture", {}).get("source", ""))
    if fixture and not fixture.exists():
        errors.append(f"{task_path}: fixture source does not exist: {fixture}")
    for artifact in data.get("artifacts", {}).get("required", []):
        schema = Path(artifact.get("schema", ""))
        if schema and not schema.exists():
            errors.append(f"{task_path}: artifact schema missing: {schema}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark task definitions")
    parser.add_argument("path", type=Path, nargs="?", default=Path("benchmarks/skills-workflow/tasks"))
    args = parser.parse_args()

    task_files = sorted(args.path.glob("*/task.json")) if args.path.is_dir() else [args.path]
    errors = [err for task in task_files for err in validate_task(task)]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {len(task_files)} task definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
