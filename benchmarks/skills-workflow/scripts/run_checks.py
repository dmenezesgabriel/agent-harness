# /// script
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness_lib import load_task, run_checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public or hidden benchmark checks for a prepared run directory")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--phase", choices=["public", "hidden"], required=True)
    args = parser.parse_args()

    task = load_task(args.task_dir)
    summary = run_checks(task, args.run_dir, args.phase)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
