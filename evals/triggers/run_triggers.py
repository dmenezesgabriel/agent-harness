#!/usr/bin/env python3
"""Measure how often skills trigger on realistic queries (Agent Skills description-trigger eval).

Each query runs --runs times, each in a fresh temp project holding skills/*/ and fixtures/.
A should-trigger query passes when its trigger rate is above 0.5; a should-not query when below.
Run with --help for flags and exit codes.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

THRESHOLD = 0.5
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None
AgentRunner = Callable[[str, Path], str]


class AgentRunError(RuntimeError):
    """The agent run produced no result, so it says nothing about triggering."""


@dataclass(frozen=True)
class Query:
    id: str
    text: str
    split: str
    expect: tuple[str, ...]


def load_queries(path: Path) -> list[Query]:
    raw = json.loads(path.read_text())
    try:
        return [Query(q["id"], q["query"], q["split"], tuple(q["expect"])) for q in raw]
    except (KeyError, TypeError) as error:
        raise ValueError(f"{str(path)!r}: each entry needs id, query, split, expect; got {error!r}") from error


def _skill_names(event: Json) -> list[str]:
    message = event.get("message") if isinstance(event, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    blocks = content if isinstance(content, list) else []
    return [b["input"]["skill"] for b in blocks if isinstance(b, dict) and b.get("name") == "Skill" and b.get("type") == "tool_use"]


def skills_invoked(stream: str) -> list[str]:
    """Skill names called in a claude stream-json transcript, in order."""
    names: list[str] = []
    for line in stream.splitlines():
        try:
            names += _skill_names(json.loads(line))
        except json.JSONDecodeError:
            continue
    return names


def trigger_rate(runs: list[list[str]], expect: tuple[str, ...]) -> float:
    """Fraction of runs that loaded an expected skill, or any skill when none is expected."""
    if not runs:
        return 0.0
    hits = sum(any(n in expect for n in r) if expect else bool(r) for r in runs)
    return hits / len(runs)


def passed(rate: float, expect: tuple[str, ...]) -> bool:
    return rate > THRESHOLD if expect else rate < THRESHOLD


def make_claude_runner(model: str) -> AgentRunner:
    def run(text: str, project: Path) -> str:
        command = ["claude", "-p", text, "--output-format", "stream-json", "--verbose", "--max-turns", "5", "--model", model]
        try:
            done = subprocess.run(command, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired as error:
            raise AgentRunError(f"claude timed out after {error.timeout}s on {text[:50]!r}") from error
        if '"type":"result"' not in done.stdout:
            raise AgentRunError(f"claude exited {done.returncode} with no result; stderr: {done.stderr[-200:]!r}")
        return done.stdout

    return run


def _prepare_project(project: Path) -> None:
    for skill in sorted((REPO / "skills").iterdir()):
        shutil.copytree(skill, project / ".claude" / "skills" / skill.name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(HERE / "fixtures", project, dirs_exist_ok=True)


def _attempt(query: Query, runner: AgentRunner) -> list[str] | None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        _prepare_project(project)
        try:
            return skills_invoked(runner(query.text, project))
        except AgentRunError as error:
            print(f"error: {query.id}: {error}", file=sys.stderr)
            return None


def evaluate(query: Query, runs: int, runner: AgentRunner) -> dict[str, object]:
    with ThreadPoolExecutor(max_workers=runs) as pool:
        attempts = list(pool.map(lambda _: _attempt(query, runner), range(runs)))
    ok = [a for a in attempts if a is not None]
    rate = trigger_rate(ok, query.expect)
    loaded = Counter(name for r in ok for name in r)
    return {"id": query.id, "split": query.split, "expect": list(query.expect), "runs_ok": len(ok),
            "errors": runs - len(ok), "loaded": dict(loaded), "rate": round(rate, 2),
            "passed": bool(ok) and passed(rate, query.expect)}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_triggers.py",
        description="Print one JSON object per query with its trigger rate and pass/fail.",
        epilog="Exit codes: 0 all queries passed, 1 some failed, 2 bad input.",
    )
    parser.add_argument("--split", choices=["train", "validation", "all"], default="all")
    parser.add_argument("--runs", type=int, default=3, help="runs per query (default 3)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--queries", type=Path, default=HERE / "queries.json")
    return parser.parse_args(argv)


def main(argv: list[str], make_runner: Callable[[str], AgentRunner] = make_claude_runner) -> int:
    args = _parse_args(argv)
    try:
        queries = [q for q in load_queries(args.queries) if args.split in ("all", q.split)]
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    runner = make_runner(args.model)
    results = [evaluate(q, args.runs, runner) for q in queries]
    for result in results:
        print(json.dumps(result), flush=True)
    summary = Counter((r["split"], r["passed"]) for r in results)
    print(f"passed: {sum(r['passed'] is True for r in results)}/{len(results)} {dict(summary)}", file=sys.stderr)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
