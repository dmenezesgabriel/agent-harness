# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import argparse
import json
import logging
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")

DEFAULT_RUNS = 3
DEFAULT_THRESHOLD = 0.5
DEFAULT_TIMEOUT = 30
DEFAULT_WORKERS = 5
EXIT_SUCCESS_THRESHOLD = 0.8


def build_command(command_template: str, query: str) -> list[str]:
    return shlex.split(command_template.replace("{query}", query))


def execute_process(command: list[str], timeout: int) -> tuple[subprocess.CompletedProcess | None, str | None]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout), None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except FileNotFoundError as e:
        return None, f"command not found: {e}"
    except Exception as e:
        return None, str(e)


def detect_trigger(output: str, pattern: str) -> bool:
    return bool(re.search(pattern, output))


def run_subprocess(command_template: str, skill_path: Path, timeout: int) -> str | None:
    cmd = shlex.split(command_template.replace("{skill_dir}", str(skill_path.resolve())))
    proc, error = execute_process(cmd, timeout)
    if error:
        return error
    if proc.returncode != 0:
        return f"command failed (exit {proc.returncode}): {proc.stderr.strip()}"
    return None


def run_query(query: str, command_template: str, detect_pattern: str, timeout: int) -> dict:
    start = time.monotonic()
    result = {"triggered": False, "duration_ms": 0, "error": None, "stdout": "", "stderr": ""}
    cmd = build_command(command_template, query)
    proc, error = execute_process(cmd, timeout)
    elapsed = int((time.monotonic() - start) * 1000)
    result["duration_ms"] = elapsed
    if error:
        result["error"] = error
    else:
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        combined = proc.stdout + "\n" + proc.stderr
        if detect_trigger(combined, detect_pattern):
            result["triggered"] = True
        if proc.returncode != 0:
            result["error"] = f"exit code {proc.returncode}"
    return result


def run_single(query: str, run_index: int, command_template: str, detect_pattern: str, timeout: int) -> dict:
    result = run_query(query, command_template, detect_pattern, timeout)
    result["run"] = run_index
    return result


def execute_install(install_command: str, skill_path: Path, timeout: int) -> str | None:
    if not install_command:
        return None
    return run_subprocess(install_command, skill_path, timeout)


def evaluate_query(
    query: str,
    should_trigger: bool,
    query_id: str | int,
    command_template: str,
    detect_pattern: str,
    runs: int,
    timeout: int,
    max_workers: int,
    threshold: float,
) -> dict:
    work_fn = partial(run_single, command_template=command_template, detect_pattern=detect_pattern, timeout=timeout)
    work_items = [(query, r) for r in range(runs)]
    run_results = []

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(work_fn, q, r_idx) for q, r_idx in work_items]
        for future in as_completed(futures):
            run_results.append(future.result())

    run_results.sort(key=lambda r: r["run"])
    triggers = sum(1 for r in run_results if r["triggered"])
    trigger_rate = triggers / runs
    passed = (trigger_rate >= threshold) if should_trigger else (trigger_rate < threshold)

    return {
        "id": query_id,
        "query": query,
        "should_trigger": should_trigger,
        "triggered_count": triggers,
        "total_runs": runs,
        "trigger_rate": trigger_rate,
        "passed": passed,
        "runs": [
            {"run": r["run"], "triggered": r["triggered"], "duration_ms": r["duration_ms"], "error": r["error"]}
            for r in run_results
        ],
    }


def print_progress(result: dict, index: int, runs: int, total_queries: int) -> None:
    done = (index + 1) * runs
    pct = result["trigger_rate"] * 100
    status = "PASS" if result["passed"] else "FAIL"
    logging.info(f"  [{done}/{total_queries}] {result['id']}: {result['triggered_count']}/{runs} ({pct:.0f}%) {status}")


def evaluate_all(
    eval_set: list[dict],
    command_template: str,
    detect_pattern: str,
    install_command: str = "",
    cleanup_command: str = "",
    skill_path: Path | None = None,
    runs: int = DEFAULT_RUNS,
    threshold: float = DEFAULT_THRESHOLD,
    timeout: int = DEFAULT_TIMEOUT,
    max_workers: int = DEFAULT_WORKERS,
) -> list[dict]:
    results = []
    total_queries = len(eval_set) * runs

    if install_command and skill_path:
        error = execute_install(install_command, skill_path, timeout)
        if error:
            logging.warning(f"  Warning: {error}")

    try:
        for i, item in enumerate(eval_set):
            result = evaluate_query(
                query=item["query"],
                should_trigger=item["should_trigger"],
                query_id=item.get("id", i),
                command_template=command_template,
                detect_pattern=detect_pattern,
                runs=runs,
                timeout=timeout,
                max_workers=max_workers,
                threshold=threshold,
            )
            results.append(result)
            print_progress(result, i, runs, total_queries)
    finally:
        if cleanup_command and skill_path:
            error = run_subprocess(cleanup_command, skill_path, timeout)
            if error:
                logging.warning(f"  Warning: cleanup failed: {error}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate skill description trigger rates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n\n"
            "  # Claude Code:\n"
            "  uv run scripts/run_eval.py --eval-set evals/trigger-evals.json \\\n"
            "    --command 'claude -p \"{query}\" --output-format json' \\\n"
            "    --detect '\"name\":\"Skill\"'\n\n"
            "  # OpenCode (example):\n"
            "  uv run scripts/run_eval.py --eval-set evals/trigger-evals.json \\\n"
            "    --command 'opencode --prompt \"{query}\"' \\\n"
            "    --detect 'skill-builder'\n\n"
            "  # With install/cleanup (copies skill to agent's skill dir):\n"
            "  uv run scripts/run_eval.py --eval-set evals/trigger-evals.json \\\n"
            "    --command 'claude -p \"{query}\"' \\\n"
            "    --detect 'skill-builder' \\\n"
            "    --install-command 'cp -r {skill_dir} ~/.claude/commands/' \\\n"
            "    --cleanup-command 'rm -rf ~/.claude/commands/skill-builder'"
        ),
    )
    parser.add_argument("--eval-set", required=True, type=Path, help="Path to trigger-evals.json")
    parser.add_argument("--command", required=True, help="Command template with {query} placeholder. E.g., 'claude -p \"{query}\"'")
    parser.add_argument("--detect", required=True, help="Regex pattern to detect skill activation in output")
    parser.add_argument("--skill-path", type=Path, default=None, help="Path to skill directory (for install/cleanup commands)")
    parser.add_argument("--install-command", default="", help="Command to run before queries. Use {skill_dir} for skill path.")
    parser.add_argument("--cleanup-command", default="", help="Command to run after queries. Use {skill_dir} for skill path.")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"Runs per query (default: {DEFAULT_RUNS})")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help=f"Pass threshold 0.0-1.0 (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout per query in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"Parallel workers (default: {DEFAULT_WORKERS})")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output path for results.json")
    args = parser.parse_args()

    if not args.eval_set.exists():
        logging.error(f"Eval set not found: {args.eval_set}")
        return 1

    if args.install_command and not args.skill_path:
        logging.error("--skill-path is required when using --install-command")
        return 1

    if "{query}" not in args.command:
        logging.error("--command must contain {query} placeholder")
        return 1

    eval_set = json.loads(args.eval_set.read_text())

    logging.info(f"Command:     {args.command}")
    logging.info(f"Detect:      /{args.detect}/")
    logging.info(f"Queries:     {len(eval_set)} ({args.runs} runs each, threshold={args.threshold})")
    if args.install_command:
        logging.info(f"Install:     {args.install_command}")
    logging.info("")

    results = evaluate_all(
        eval_set, args.command, args.detect,
        install_command=args.install_command,
        cleanup_command=args.cleanup_command,
        skill_path=args.skill_path,
        runs=args.runs, threshold=args.threshold,
        timeout=args.timeout, max_workers=args.workers,
    )

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    pass_rate = passed / total if total > 0 else 0

    output = {
        "config": {
            "command": args.command,
            "detect_pattern": args.detect,
            "runs_per_query": args.runs,
            "pass_threshold": args.threshold,
            "timeout_seconds": args.timeout,
        },
        "summary": {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(pass_rate, 4),
        },
        "results": results,
    }

    output_path = args.output or Path("trigger-results.json")
    output_path.write_text(json.dumps(output, indent=2))
    logging.info(f"\nResults written to: {output_path}")
    logging.info(f"Pass rate: {passed}/{total} ({pass_rate*100:.0f}%)")

    return 0 if pass_rate >= EXIT_SUCCESS_THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
