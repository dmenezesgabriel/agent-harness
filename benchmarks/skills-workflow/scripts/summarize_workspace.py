# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness_lib import load_task, summarize_task_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize one benchmark task workspace")
    parser.add_argument("task_workspace", type=Path)
    parser.add_argument("--task-dir", type=Path, help="Optional task definition dir. Defaults to matching tasks/<task-id>.")
    parser.add_argument("--run-name", default="run-1")
    args = parser.parse_args()

    task_dir = args.task_dir or Path("benchmarks/skills-workflow/tasks") / args.task_workspace.name
    task = load_task(task_dir)
    summary = summarize_task_workspace(task, args.task_workspace, args.run_name)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
