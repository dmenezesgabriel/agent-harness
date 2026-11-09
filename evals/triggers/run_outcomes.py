#!/usr/bin/env python3
"""Compare what an agent produces on the same coding tasks with and without the skills.

Each (task, arm) attempt runs in a fresh sandbox of the app fixtures; deterministic checks
(outcome_checks.py) then score the finished project. Arms: `none` (no skills installed),
`skills` (installed, agent decides) and `router` (prompt prefixed with /engineering-mode).
Attempts run serially with a pause between them, to stay under rate limits.
Run with --help for flags; exit 0 always unless input is bad (2).
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess  # nosec B404 -- only for the TimeoutExpired type raised by the checks
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # `python3 -I` leaves the script's own directory off sys.path; the siblings below need it

from outcome_checks import Spec, run_check  # noqa: E402
from run_triggers import (  # noqa: E402
    AgentRunError,
    AgentRunner,
    Json,
    make_devin_runner,
    prepare_project,
    skills_invoked_atif,
    wilson,
)

FIXTURES = (HERE / "fixtures", HERE / "app" / "fixtures")
ARMS = ("none", "skills", "router")
IGNORED_PARTS = {".claude", "__pycache__", ".atif-export.json"}
# A shell write into tests/ or src/: redirection, tee, or sed -i with a quoted script.
EXEC_WRITE = re.compile(r"(?:>>?\s*|\btee\s+(?:-a\s+)?|\bsed\s+-i\S*\s+(?:-e\s+)?(?:'[^']*'|\"[^\"]*\")\s+)\S*?\b(tests|src)/")
TEST_RUN = re.compile(r"\b(?:unittest|pytest)\b")
# unittest prints FAILED (failures=N) or ERROR/Error lines; pytest prints "N failed"; a crash prints Traceback.
RED_OUTPUT = re.compile(r"\bFAILED\b|\bfailed\b|\bERROR\b|Error\b|Traceback")


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    checks: tuple[Spec, ...]


def load_tasks(path: Path) -> list[Task]:
    """Tasks from tasks.json; ValueError names the offending entry."""
    raw = cast("list[dict[str, object]]", json.loads(path.read_text()))
    tasks: list[Task] = []
    for entry in raw:
        checks = entry.get("checks")
        if not isinstance(entry.get("id"), str) or not isinstance(entry.get("prompt"), str) or not isinstance(checks, list):
            raise ValueError(f"{str(path)!r}: each task needs string id, string prompt and list checks; got {entry!r}")
        tasks.append(Task(str(entry["id"]), str(entry["prompt"]), tuple(cast("list[Spec]", checks))))
    return tasks


def arm_prompt(task: Task, arm: str) -> str:
    return f"/engineering-mode {task.prompt}" if arm == "router" else task.prompt


def _files(root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not IGNORED_PARTS & set(path.relative_to(root).parts):
            found[str(path.relative_to(root))] = path.read_text(errors="replace")
    return found


def project_diff(reference: Path, project: Path) -> str:
    """Unified diff of every file the agent added, changed or removed; the evidence behind the checks."""
    before, after = _files(reference), _files(project)
    chunks = [
        "".join(difflib.unified_diff(before.get(name, "").splitlines(True), after.get(name, "").splitlines(True), f"a/{name}", f"b/{name}"))
        for name in sorted(before.keys() | after.keys())
        if before.get(name) != after.get(name)
    ]
    return "".join(chunks)


def _touched(call: Json) -> str | None:
    """'tests' or 'src' when a devin tool call writes into that directory, else None."""
    if not isinstance(call, dict):
        return None
    args = call.get("arguments")
    args = args if isinstance(args, dict) else {}
    if call.get("function_name") in ("edit", "write"):
        path = str(args.get("file_path", ""))
        return "tests" if "/tests/" in path else "src" if "/src/" in path else None
    match = EXEC_WRITE.search(str(args.get("command", ""))) if call.get("function_name") == "exec" else None
    return match.group(1) if match else None


def _tool_calls(raw: str) -> list[Json]:
    """Every tool call of an ATIF export, in order."""
    doc = cast("dict[str, Json]", json.loads(raw))
    steps = doc.get("steps")
    calls: list[Json] = []
    for step in steps if isinstance(steps, list) else []:
        step_calls = step.get("tool_calls") if isinstance(step, dict) else None
        calls += step_calls if isinstance(step_calls, list) else []
    return calls


def _first_writes(calls: list[Json]) -> dict[str, int]:
    """Index of the first call writing into tests/ and into src/, for the kinds present."""
    first: dict[str, int] = {}
    for index, call in enumerate(calls):
        touched = _touched(call)
        if touched:
            first.setdefault(touched, index)
    return first


def edit_order(raw: str) -> str | None:
    """'test-first' or 'src-first' from the first write into each of tests/ and src/ (a heuristic); None if either is missing."""
    first = _first_writes(_tool_calls(raw))
    if "tests" not in first or "src" not in first:
        return None
    return "test-first" if first["tests"] < first["src"] else "src-first"


def _outputs_by_call(raw: str) -> dict[str, str]:
    """Tool output text keyed by the id of the call that produced it."""
    doc = cast("dict[str, Json]", json.loads(raw))
    steps = doc.get("steps")
    outputs: dict[str, str] = {}
    for step in steps if isinstance(steps, list) else []:
        observation = step.get("observation") if isinstance(step, dict) else None
        results = observation.get("results") if isinstance(observation, dict) else None
        for result in results if isinstance(results, list) else []:
            if isinstance(result, dict):
                outputs[str(result.get("source_call_id"))] = str(result.get("content", ""))
    return outputs


def _is_red_run(call: Json, outputs: dict[str, str]) -> bool:
    """A unittest/pytest exec whose output shows a failure."""
    if not isinstance(call, dict) or call.get("function_name") != "exec":
        return False
    args = call.get("arguments")
    command = str(args.get("command", "")) if isinstance(args, dict) else ""
    return bool(TEST_RUN.search(command) and RED_OUTPUT.search(outputs.get(str(call.get("tool_call_id")), "")))


def red_first(raw: str) -> bool:
    """True when a test run between the first write into tests/ and the first into src/ showed a failure: red seen before green.

    Stricter than edit_order: a test written first but never run failing does not count. Output fetched later
    (a backgrounded run read via another tool) is missed, so this undercounts.
    """
    calls = _tool_calls(raw)
    first = _first_writes(calls)
    if "tests" not in first or "src" not in first or first["tests"] > first["src"]:
        return False
    outputs = _outputs_by_call(raw)
    return any(_is_red_run(call, outputs) for call in calls[first["tests"]:first["src"]])


def score_checks(task: Task, project: Path, reference: Path) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for spec in task.checks:
        try:
            result = run_check(spec, project, reference)
            results[str(spec["name"])] = {"passed": result.passed, "value": result.value}
        except subprocess.TimeoutExpired:
            results[str(spec["name"])] = {"passed": False, "value": None, "error": "timeout"}
    return results


def attempt(task: Task, arm: str, runner: AgentRunner, reference: Path, keep: Path) -> dict[str, object]:
    """One agent run in a fresh sandbox, scored; the transcript lands in keep/<task>-<arm>/."""
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        prepare_project(project, FIXTURES, with_skills=arm != "none")
        try:
            raw = runner(arm_prompt(task, arm), project)
        except AgentRunError as error:
            print(f"error: {task.id}/{arm}: {error}", file=sys.stderr)
            return {"task": task.id, "arm": arm, "error": str(error)}
        (keep / f"{task.id}-{arm}").mkdir(parents=True, exist_ok=True)
        (keep / f"{task.id}-{arm}" / f"{time.time_ns()}.json").write_text(raw)
        checks = score_checks(task, project, reference)
        order = edit_order(raw)
        if order is not None:
            checks["test_first"] = {"passed": order == "test-first", "value": None}
            checks["red_first"] = {"passed": red_first(raw), "value": None}
        return {"task": task.id, "arm": arm, "loaded": skills_invoked_atif(raw), "checks": checks,
                "diff": project_diff(reference, project)}


def run(tasks: list[Task], arms: list[str], runs: int, runner: AgentRunner, keep: Path, delay: float) -> None:
    """Round-robin over runs, then tasks, then arms, so drift or throttling hits every arm alike."""
    keep.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as ref:
        reference = Path(ref)
        prepare_project(reference, FIXTURES, with_skills=False)
        for _ in range(runs):
            for task in tasks:
                for arm in arms:
                    record = attempt(task, arm, runner, reference, keep)
                    with open(keep / "outcomes.jsonl", "a") as handle:
                        handle.write(json.dumps(record) + "\n")
                    time.sleep(delay)


def _ok_records(path: Path) -> dict[tuple[str, str], list[dict[str, Json]]]:
    grouped: dict[tuple[str, str], list[dict[str, Json]]] = defaultdict(list)
    for line in path.read_text().splitlines():
        record = cast("dict[str, Json]", json.loads(line))
        grouped[(str(record["task"]), str(record["arm"]))].append(record)
    return grouped


def _check_stats(records: list[dict[str, Json]]) -> dict[str, dict[str, object]]:
    """Per check: runs, passes, 95% Wilson CI and mean value over the successful runs."""
    ok = [cast("dict[str, dict[str, Json]]", r["checks"]) for r in records if "checks" in r]
    stats: dict[str, dict[str, object]] = {}
    for name in sorted({name for checks in ok for name in checks}):
        outcomes = [checks[name] for checks in ok if name in checks]
        passes = sum(o["passed"] is True for o in outcomes)
        lo, hi = wilson(passes, len(outcomes))
        values = [float(str(o["value"])) for o in outcomes if isinstance(o.get("value"), (int, float))]
        stats[name] = {"runs": len(outcomes), "passes": passes, "ci95": [round(lo, 2), round(hi, 2)],
                       "mean_value": round(sum(values) / len(values), 2) if values else None}
    return stats


def score(keep: Path) -> int:
    """One JSON line per (task, arm) from keep/outcomes.jsonl, then a compact pass-count table on stderr."""
    try:
        grouped = _ok_records(keep / "outcomes.jsonl")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for (task, arm), records in sorted(grouped.items()):
        stats = _check_stats(records)
        errors = sum("error" in r for r in records)
        print(json.dumps({"task": task, "arm": arm, "runs_ok": len(records) - errors, "errors": errors, "checks": stats}))
        cells = " ".join(f"{name}={s['passes']}/{s['runs']}" for name, s in stats.items())
        print(f"{task:14} {arm:7} {cells}", file=sys.stderr)
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_outcomes.py", description="Compare agent outcomes on the same coding tasks with and without the skills.")
    parser.add_argument("--tasks", type=Path, default=HERE / "outcomes" / "tasks.json")
    parser.add_argument("--arms", default=",".join(ARMS), help=f"comma-separated subset of {ARMS}")
    parser.add_argument("--runs", type=int, default=4, help="attempts per (task, arm) (default 4)")
    parser.add_argument("--model", default="swe-2-medium")
    parser.add_argument("--permission-mode", default="smart", help="devin permission mode; edits and test runs need smart")
    parser.add_argument("--timeout", type=int, default=600, help="seconds per devin attempt")
    parser.add_argument("--delay", type=float, default=10.0, help="seconds to wait after each attempt")
    parser.add_argument("--keep-transcripts", type=Path, metavar="DIR", required=True,
                        help="where outcomes.jsonl and transcripts accumulate (and are scored from)")
    parser.add_argument("--score", action="store_true", help="aggregate DIR/outcomes.jsonl instead of running the agent")
    return parser.parse_args(argv)


def main(argv: list[str], make_runner: Callable[[str, str, int], AgentRunner] = lambda m, p, t: make_devin_runner(m, p, t)) -> int:
    args = _parse_args(argv)
    arms = args.arms.split(",")
    if args.score:
        return score(args.keep_transcripts)
    if not set(arms) <= set(ARMS):
        print(f"error: --arms {args.arms!r}; expected a subset of {ARMS}", file=sys.stderr)
        return 2
    try:
        tasks = load_tasks(args.tasks)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    runner = make_runner(args.model, args.permission_mode, args.timeout)
    run(tasks, arms, args.runs, runner, args.keep_transcripts, args.delay)
    return score(args.keep_transcripts)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
