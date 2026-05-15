# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
from pathlib import Path

from harness_lib import get_task_workspace, initialize_run, load_task, summarize_task_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a paired benchmark workspace scaffold for one task")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--iteration", default="iteration-1")
    parser.add_argument("--workspace-root", type=Path, default=Path(".workspaces/skills-workflow-benchmarks"))
    parser.add_argument("--run-name", default="run-1")
    args = parser.parse_args()

    task = load_task(args.task_dir)
    task_workspace = get_task_workspace(task, args.task_dir, args.workspace_root, args.iteration)
    for config in task["run"]["allowed_configurations"]:
        initialize_run(args.task_dir, task, task_workspace, config, args.run_name)
    summarize_task_workspace(task, task_workspace, args.run_name)
    print(task_workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
