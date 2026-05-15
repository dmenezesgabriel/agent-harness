# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness_lib import (
    ExecutionOptions,
    execute_run,
    finalize_run,
    get_task_workspace,
    initialize_run,
    load_task,
    summarize_task_workspace,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize or execute/finalize paired benchmark runs for one task")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--iteration", default="iteration-1")
    parser.add_argument("--workspace-root", type=Path, default=Path(".workspaces/skills-workflow-benchmarks"))
    parser.add_argument("--run-name", default="run-1")
    parser.add_argument("--reinitialize", action="store_true")
    parser.add_argument("--manual-only", action="store_true", help="Skip Pi execution and only finalize existing completion files")
    parser.add_argument("--pi-bin", default="pi")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--thinking")
    args = parser.parse_args()

    task = load_task(args.task_dir)
    task_workspace = get_task_workspace(task, args.task_dir, args.workspace_root, args.iteration)
    task_workspace.mkdir(parents=True, exist_ok=True)
    (task_workspace / "task-metadata.json").write_text(json.dumps(task, indent=2) + "\n")

    execution_options = ExecutionOptions(
        pi_bin=args.pi_bin,
        provider=args.provider,
        model=args.model,
        thinking=args.thinking,
    )

    run_results = []
    for configuration in task["run"]["allowed_configurations"]:
        run_dir = task_workspace / configuration / args.run_name
        if args.reinitialize or not (run_dir / "run-metadata.json").exists():
            initialize_run(args.task_dir, task, task_workspace, configuration, args.run_name)

        execution = None
        if not args.manual_only:
            execution = execute_run(task, run_dir, execution_options)

        summary = finalize_run(task, run_dir)
        if execution is not None:
            summary = {"execution": execution, "finalization": summary}
        run_results.append(summary)

    paired_summary = summarize_task_workspace(task, task_workspace, args.run_name)
    payload = {
        "task_workspace": str(task_workspace),
        "runs": run_results,
        "benchmark_summary": paired_summary,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
