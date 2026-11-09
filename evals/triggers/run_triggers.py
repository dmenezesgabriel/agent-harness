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
import re
import shutil
import subprocess  # nosec B404 -- needed to invoke the claude/devin CLIs; argv list form, never shell
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


def _loads(text: str) -> Json:
    """json.loads result retyped as this module's Json union."""
    return json.loads(text)


class AgentRunError(RuntimeError):
    """The agent run produced no result, so it says nothing about triggering."""


@dataclass(frozen=True)
class Query:
    id: str
    text: str
    split: str
    expect: tuple[str, ...]


def _query(item: Json) -> Query:
    """Build a Query from one queries.json entry; TypeError names the offending field."""
    if not isinstance(item, dict):
        raise TypeError(f"{item!r} is not an object")
    values: dict[str, str] = {}
    for field in ("id", "query", "split"):
        value = item.get(field)
        if not isinstance(value, str):
            raise TypeError(f"{item!r}: {field!r} must be a string")
        values[field] = value
    expect = item.get("expect")
    if not isinstance(expect, list) or not all(isinstance(e, str) for e in expect):
        raise TypeError(f"{item!r}: 'expect' must be a list of strings")
    names = [e for e in expect if isinstance(e, str)]
    return Query(values["id"], values["query"], values["split"], tuple(names))


def load_queries(path: Path) -> list[Query]:
    raw = _loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"{str(path)!r}: expected a JSON array of query objects; got {type(raw).__name__}")
    try:
        return [_query(item) for item in raw]
    except TypeError as error:
        raise ValueError(f"{str(path)!r}: each entry needs id, query, split, expect; got {error!r}") from error


SKILL_FILE = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")


def _unique(names: list[str]) -> list[str]:
    """Order-preserving de-dup so `loaded` counts runs, not repeat loads within one run."""
    return list(dict.fromkeys(names))


def _file_read_skill(tool_input: Json) -> list[str]:
    """Skills whose SKILL.md a read/exec call opened; the spec counts a SKILL.md load as a trigger."""
    return SKILL_FILE.findall(json.dumps(tool_input))


def _skill_names(event: Json) -> list[str]:
    message = event.get("message") if isinstance(event, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    blocks = content if isinstance(content, list) else []
    names: list[str] = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        tool_input = block.get("input")
        if block.get("name") in ("Read", "Bash"):
            names += _file_read_skill(tool_input)
        elif block.get("name") == "Skill":
            skill = tool_input.get("skill") if isinstance(tool_input, dict) else None
            if isinstance(skill, str):
                names.append(skill)
    return names


def skills_invoked(stream: str) -> list[str]:
    """Skills loaded in a claude stream-json transcript (Skill calls and SKILL.md reads), first-load order."""
    names: list[str] = []
    for line in stream.splitlines():
        try:
            names += _skill_names(_loads(line))
        except json.JSONDecodeError:
            continue
    return _unique(names)


def _atif_skill_names(tool_calls: Json) -> list[str]:
    calls = tool_calls if isinstance(tool_calls, list) else []
    names: list[str] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        args = call.get("arguments")
        if isinstance(args, str):
            try:
                args = _loads(args)
            except json.JSONDecodeError:
                continue
        if call.get("function_name") in ("read", "exec"):
            names += _file_read_skill(args)
        elif call.get("function_name") == "skill":
            skill = args.get("skill") if isinstance(args, dict) else None
            if isinstance(skill, str):
                names.append(skill)
    return names


def skills_invoked_atif(stream: str) -> list[str]:
    """Skills loaded in a devin --export ATIF transcript (skill calls and SKILL.md reads), first-load order."""
    try:
        doc = _loads(stream)
    except json.JSONDecodeError:
        return []
    steps = doc.get("steps") if isinstance(doc, dict) else None
    names: list[str] = []
    for step in steps if isinstance(steps, list) else []:
        if isinstance(step, dict):
            names += _atif_skill_names(step.get("tool_calls"))
    return _unique(names)


def _str_list(value: Json) -> list[str]:
    """String members of a JSON list; empty list for anything else."""
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


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
            done = subprocess.run(command, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240)  # noqa: S603  # nosec B603 -- fixed argv list; query text is an argv element, never shell-expanded
        except subprocess.TimeoutExpired as error:
            raise AgentRunError(f"claude timed out after {error.timeout}s on {text[:50]!r}") from error
        if '"type":"result"' not in done.stdout:
            raise AgentRunError(f"claude exited {done.returncode} with no result; stderr: {done.stderr[-200:]!r}")
        return done.stdout

    return run


def make_devin_runner(model: str, permission_mode: str | None = None, timeout: int = 300) -> AgentRunner:
    def run(text: str, project: Path) -> str:
        export = project / ".atif-export.json"
        command = ["devin", "-p", "--model", model, "--export", str(export),
                   "--respect-workspace-trust", "false"]
        if permission_mode:
            command += ["--permission-mode", permission_mode]
        command += ["--", text]
        try:
            done = subprocess.run(command, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)  # noqa: S603  # nosec B603 -- fixed argv list; query text is an argv element, never shell-expanded
        except subprocess.TimeoutExpired as error:
            raise AgentRunError(f"devin timed out after {error.timeout}s on {text[:50]!r}") from error
        try:
            atif = export.read_text()
            doc: Json = _loads(atif)
        except (OSError, json.JSONDecodeError) as error:
            raise AgentRunError(
                f"devin exited {done.returncode} with no readable ATIF export; stderr: {done.stderr[-200:]!r}"
            ) from error
        steps = doc.get("steps") if isinstance(doc, dict) else None
        if not steps:
            raise AgentRunError(f"devin exited {done.returncode} with no ATIF steps; stderr: {done.stderr[-200:]!r}")
        return atif

    return run


def prepare_project(project: Path, fixtures: tuple[Path, ...], with_skills: bool = True) -> None:
    """Fill a sandbox with the repo's skills (unless `with_skills` is False) and the fixture layers, in order."""
    for skill in sorted((REPO / "skills").iterdir()) if with_skills else []:
        shutil.copytree(skill, project / ".claude" / "skills" / skill.name, ignore=shutil.ignore_patterns("__pycache__", "mutants"))
    for layer in fixtures:
        shutil.copytree(layer, project, dirs_exist_ok=True)


def _record(keep: Path, query: Query, raw: str, loaded: list[str] | None, ext: str) -> None:
    """Persist one attempt's transcript plus a runs.jsonl line for --score-transcripts."""
    suffix = ext if loaded is not None else ".err.txt"
    (keep / query.id / f"{time.time_ns()}{suffix}").write_text(raw)
    record = {"id": query.id, "loaded": loaded} if loaded is not None else {"id": query.id, "error": raw}
    with open(keep / "runs.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")


def _attempt(query: Query, runner: AgentRunner, parse: TranscriptParser,
             keep: Path | None, ext: str, delay: float, fixtures: tuple[Path, ...]) -> list[str] | None:
    raw, loaded = "", None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            prepare_project(project, fixtures)
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
             delay: float = 0.0, keep: Path | None = None, ext: str = ".jsonl",
             fixtures: tuple[Path, ...] = (HERE / "fixtures",)) -> dict[str, object]:
    """Run `query` `runs` times; with `invoke`, the user-invoked skill is not counted as a trigger."""
    if keep:
        (keep / query.id).mkdir(parents=True, exist_ok=True)
    def attempt(_: int) -> list[str] | None:
        return _attempt(query, runner, parse, keep, ext, delay, fixtures)

    with ThreadPoolExecutor(max_workers=workers or runs) as pool:
        attempts = list(pool.map(attempt, range(runs)))
    ok = [[name for name in a if name != invoke] for a in attempts if a is not None]
    rate = trigger_rate(ok, query.expect)
    loaded = Counter(name for r in ok for name in r)
    return {"id": query.id, "split": query.split, "expect": list(query.expect), "runs_ok": len(ok),
            "errors": runs - len(ok), "loaded": dict(loaded), "rate": round(rate, 2),
            "passed": bool(ok) and passed(rate, query.expect)}


def _load_records(keep: Path, queries: list[Query]) -> dict[str, list[Json]] | None:
    """runs.jsonl records grouped by query id; None (after printing why) when unreadable."""
    try:
        lines = (keep / "runs.jsonl").read_text().splitlines()
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return None
    records: dict[str, list[Json]] = {q.id: [] for q in queries}
    for line in lines:
        try:
            record = _loads(line)
        except json.JSONDecodeError:
            continue
        rid = record.get("id") if isinstance(record, dict) else None
        if isinstance(rid, str) and rid in records:
            records[rid].append(record)
    return records


def _ok_runs(recs: list[Json], invoke: str | None) -> list[list[str]]:
    """Loaded-skill lists of successful attempts, without the user-invoked skill."""
    loaded = [_str_list(r["loaded"]) for r in recs if isinstance(r, dict) and isinstance(r.get("loaded"), list)]
    return [[name for name in run if name != invoke] for run in loaded]


def score(keep: Path, queries: list[Query], invoke: str | None = None, pool: bool = False) -> int:
    """Recompute results from a --keep-transcripts directory, with 95% Wilson CIs; `pool` groups by expected skill."""
    records = _load_records(keep, queries)
    if records is None:
        return 2
    runs = {q.id: _ok_runs(records[q.id], invoke) for q in queries}
    if pool:
        return _report_pooled(pooled(queries, runs))
    results: list[dict[str, object]] = []
    for query in queries:
        ok = runs[query.id]
        lo, hi = wilson(sum(_hit(r, query.expect) for r in ok), len(ok))
        rate = trigger_rate(ok, query.expect)
        loaded = Counter(name for r in ok for name in r)
        results.append({"id": query.id, "split": query.split, "expect": list(query.expect),
                        "runs_ok": len(ok), "errors": len(records[query.id]) - len(ok), "loaded": dict(loaded),
                        "rate": round(rate, 2), "ci95": [round(lo, 2), round(hi, 2)],
                        "passed": bool(ok) and passed(rate, query.expect)})
    return _report(results)


def pooled(queries: list[Query], runs_by_query: dict[str, list[list[str]]]) -> list[dict[str, object]]:
    """Pool successful runs of queries that share an `expect` set, with a 95% Wilson CI.

    `conclusive` means the CI sits fully on the passing side of THRESHOLD, so a pooled
    group can settle what three runs of one query cannot. Example: two queries x 3 runs,
    all hits, give CI [0.61, 1.0].
    """
    groups: dict[tuple[str, ...], list[Query]] = {}
    for query in queries:
        groups.setdefault(query.expect, []).append(query)
    results: list[dict[str, object]] = []
    for expect, members in groups.items():
        ok = [run for q in members for run in runs_by_query[q.id]]
        hits = sum(_hit(run, expect) for run in ok)
        lo, hi = wilson(hits, len(ok))
        conclusive = bool(ok) and (lo > THRESHOLD if expect else hi < THRESHOLD)
        results.append({"expect": list(expect), "queries": [q.id for q in members], "runs": len(ok),
                        "hits": hits, "rate": round(hits / len(ok), 2) if ok else 0.0,
                        "ci95": [round(lo, 2), round(hi, 2)], "conclusive": conclusive,
                        "passed": bool(ok) and passed(hits / len(ok), expect)})
    return results


def _report_pooled(results: list[dict[str, object]]) -> int:
    for result in results:
        print(json.dumps(result), flush=True)
    conclusive = sum(r["conclusive"] is True for r in results)
    print(f"pooled groups: {len(results)}, conclusive: {conclusive}, passed: {sum(r['passed'] is True for r in results)}",
          file=sys.stderr)
    return 0 if all(r["passed"] and r["conclusive"] for r in results) else 1


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
    parser.add_argument("--fixtures", type=Path, action="append", metavar="DIR",
                        help="project files copied into each attempt's sandbox; repeat to layer dirs in order "
                             "(default: evals/triggers/fixtures)")
    parser.add_argument("--pooled", action="store_true",
                        help="with --score-transcripts: pool runs of queries sharing an expect set and report a CI per group")
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
        return score(args.score_transcripts, queries, args.invoke, args.pooled)
    if args.invoke:
        queries = [Query(q.id, f"/{args.invoke} {q.text}", q.split, q.expect) for q in queries]
    devin = args.harness == "devin"
    model: str = args.model
    permission_mode: str | None = args.permission_mode
    runs: int = args.runs
    invoke: str | None = args.invoke
    workers: int | None = args.workers
    delay: float = args.delay
    keep: Path | None = args.keep_transcripts
    ext = ".json" if devin else ".jsonl"

    def factory(m: str) -> AgentRunner:
        return make_devin_runner(m, permission_mode) if devin else make_claude_runner(m)

    build_runner = make_runner if make_runner is not None else factory
    parse = skills_invoked_atif if devin else skills_invoked
    runner = build_runner(model)
    results = [evaluate(q, runs, runner, invoke, parse, workers, delay, keep, ext, tuple(args.fixtures or [HERE / "fixtures"]))
               for q in queries]
    return _report(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
