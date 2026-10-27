#!/usr/bin/env python3
"""Measure how often skills trigger on realistic queries (Agent Skills description-trigger eval).

Each query runs --runs times, each in a fresh temp project holding skills/*/ and fixtures/.
A should-trigger query passes when its trigger rate is above 0.5; a should-not query when below.
Run with --help for flags and exit codes.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
import time
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
TranscriptParser = Callable[[str], list[str]]


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


def _atif_skill_names(tool_calls: Json) -> list[str]:
    calls = tool_calls if isinstance(tool_calls, list) else []
    names: list[str] = []
    for call in calls:
        if not isinstance(call, dict) or call.get("function_name") != "skill":
            continue
        args = call.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                continue
        if isinstance(args, dict) and isinstance(args.get("skill"), str):
            names.append(args["skill"])
    return names


def skills_invoked_atif(stream: str) -> list[str]:
    """Skill names invoked in a devin --export ATIF transcript, in order."""
    try:
        doc = json.loads(stream)
    except json.JSONDecodeError:
        return []
    steps = doc.get("steps") if isinstance(doc, dict) else None
    names: list[str] = []
    for step in steps if isinstance(steps, list) else []:
        if isinstance(step, dict):
            names += _atif_skill_names(step.get("tool_calls"))
    return names


def _hit(names: list[str], expect: tuple[str, ...]) -> bool:
    return any(n in expect for n in names) if expect else bool(names)


def trigger_rate(runs: list[list[str]], expect: tuple[str, ...]) -> float:
    """Fraction of runs that loaded an expected skill, or any skill when none is expected."""
    if not runs:
        return 0.0
    return sum(_hit(r, expect) for r in runs) / len(runs)


def passed(rate: float, expect: tuple[str, ...]) -> bool:
    return rate > THRESHOLD if expect else rate < THRESHOLD


def wilson(hits: int, n: int) -> tuple[float, float]:
    """95% Wilson score interval bounds for hits/n."""
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.96, hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


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


def make_devin_runner(model: str, permission_mode: str | None = None) -> AgentRunner:
    def run(text: str, project: Path) -> str:
        export = project / ".atif-export.json"
        command = ["devin", "-p", "--model", model, "--export", str(export),
                   "--respect-workspace-trust", "false"]
        if permission_mode:
            command += ["--permission-mode", permission_mode]
        command += ["--", text]
        try:
            done = subprocess.run(command, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as error:
            raise AgentRunError(f"devin timed out after {error.timeout}s on {text[:50]!r}") from error
        try:
            atif = export.read_text()
            doc = json.loads(atif)
            steps = doc.get("steps") if isinstance(doc, dict) else None
        except (OSError, json.JSONDecodeError):
            steps = None
        if not steps:
            raise AgentRunError(f"devin exited {done.returncode} with no ATIF steps; stderr: {done.stderr[-200:]!r}")
        return atif

    return run


def _prepare_project(project: Path) -> None:
    for skill in sorted((REPO / "skills").iterdir()):
        shutil.copytree(skill, project / ".claude" / "skills" / skill.name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(HERE / "fixtures", project, dirs_exist_ok=True)


def _record(keep: Path, query: Query, raw: str, loaded: list[str] | None, ext: str) -> None:
    """Persist one attempt's transcript plus a runs.jsonl line for --score-transcripts."""
    suffix = ext if loaded is not None else ".err.txt"
    (keep / query.id / f"{time.time_ns()}{suffix}").write_text(raw)
    record = {"id": query.id, "loaded": loaded} if loaded is not None else {"id": query.id, "error": raw}
    with open(keep / "runs.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")


def _attempt(query: Query, runner: AgentRunner, parse: TranscriptParser,
             keep: Path | None, ext: str, delay: float) -> list[str] | None:
    raw, loaded = "", None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            _prepare_project(project)
            raw = runner(query.text, project)
            loaded = parse(raw)
    except AgentRunError as error:
        raw = str(error)
        print(f"error: {query.id}: {error}", file=sys.stderr)
    if delay:
        time.sleep(delay)
    if keep:
        _record(keep, query, raw, loaded, ext)
    return loaded


def evaluate(query: Query, runs: int, runner: AgentRunner, invoke: str | None = None,
             parse: TranscriptParser = skills_invoked, workers: int | None = None,
             delay: float = 0.0, keep: Path | None = None, ext: str = ".jsonl") -> dict[str, object]:
    """Run `query` `runs` times; with `invoke`, the user-invoked skill is not counted as a trigger."""
    if keep:
        (keep / query.id).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers or runs) as pool:
        attempts = list(pool.map(lambda _: _attempt(query, runner, parse, keep, ext, delay), range(runs)))
    ok = [[name for name in a if name != invoke] for a in attempts if a is not None]
    rate = trigger_rate(ok, query.expect)
    loaded = Counter(name for r in ok for name in r)
    return {"id": query.id, "split": query.split, "expect": list(query.expect), "runs_ok": len(ok),
            "errors": runs - len(ok), "loaded": dict(loaded), "rate": round(rate, 2),
            "passed": bool(ok) and passed(rate, query.expect)}


def score(keep: Path, queries: list[Query]) -> int:
    """Recompute per-query results from a --keep-transcripts directory, with 95% Wilson CIs."""
    try:
        lines = (keep / "runs.jsonl").read_text().splitlines()
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    records: dict[str, list[Json]] = {q.id: [] for q in queries}
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("id") in records:
            records[record["id"]].append(record)
    results = []
    for query in queries:
        recs = records[query.id]
        ok = [r["loaded"] for r in recs if isinstance(r.get("loaded"), list)]
        lo, hi = wilson(sum(_hit(r, query.expect) for r in ok), len(ok))
        rate = trigger_rate(ok, query.expect)
        loaded = Counter(name for r in ok for name in r)
        results.append({"id": query.id, "split": query.split, "expect": list(query.expect),
                        "runs_ok": len(ok), "errors": len(recs) - len(ok), "loaded": dict(loaded),
                        "rate": round(rate, 2), "ci95": [round(lo, 2), round(hi, 2)],
                        "passed": bool(ok) and passed(rate, query.expect)})
    return _report(results)


def _report(results: list[dict[str, object]]) -> int:
    for result in results:
        print(json.dumps(result), flush=True)
    summary = Counter((r["split"], r["passed"]) for r in results)
    print(f"passed: {sum(r['passed'] is True for r in results)}/{len(results)} {dict(summary)}", file=sys.stderr)
    return 0 if all(r["passed"] for r in results) else 1


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
    parser.add_argument("--invoke", metavar="SKILL", help="prefix each query with /SKILL, as a user invoking it")
    parser.add_argument("--harness", choices=["claude", "devin"], default="claude")
    parser.add_argument("--permission-mode", default=None, metavar="MODE",
                        help="devin permission mode; auto-rejected tools end -p runs early, so 'smart' yields complete answers")
    parser.add_argument("--workers", type=int, default=None, help="parallel attempts per query (default: --runs)")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to wait after each attempt")
    parser.add_argument("--keep-transcripts", type=Path, metavar="DIR",
                        help="save each attempt's transcript under DIR and append DIR/runs.jsonl")
    parser.add_argument("--score-transcripts", type=Path, metavar="DIR",
                        help="aggregate DIR/runs.jsonl instead of running the agent")
    return parser.parse_args(argv)


def main(argv: list[str], make_runner: Callable[[str], AgentRunner] | None = None) -> int:
    args = _parse_args(argv)
    try:
        queries = [q for q in load_queries(args.queries) if args.split in ("all", q.split)]
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.score_transcripts:
        return score(args.score_transcripts, queries)
    if args.invoke:
        queries = [Query(q.id, f"/{args.invoke} {q.text}", q.split, q.expect) for q in queries]
    devin = args.harness == "devin"
    factory = make_runner or (lambda m: make_devin_runner(m, args.permission_mode) if devin else make_claude_runner(m))
    parse = skills_invoked_atif if devin else skills_invoked
    runner = factory(args.model)
    results = [evaluate(q, args.runs, runner, args.invoke, parse, args.workers,
                        args.delay, args.keep_transcripts, ".json" if devin else ".jsonl")
               for q in queries]
    return _report(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
