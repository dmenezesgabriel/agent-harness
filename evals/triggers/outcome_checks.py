"""Deterministic outcome checks, run on a sandbox after an agent finished its task.

Each check takes the finished `project`, the untouched `reference` (the fixtures the agent started
from) and its JSON `spec` from tasks.json, and returns a CheckResult. No LLM judge: a check either
runs code or counts findings, so the same project always scores the same.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404 -- runs the agent's own tests and the repo's find-* scripts; argv lists, never shell
import sys
import tempfile
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# -B: -I ignores PYTHONDONTWRITEBYTECODE, and a same-size, same-second file swap (mutant, then original)
# would otherwise be served from a stale .pyc.
UNITTEST = [sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."]
IMPORT_FAILURE = re.compile(r"ImportError|ModuleNotFoundError|cannot import name|Cannot find module")
Spec = dict[str, object]


@dataclass(frozen=True)
class Suite:
    """How one language's tests run: the dir the runner starts in, its argv, where tests live and how one is spelled."""
    root: str
    command: tuple[str, ...]
    only: str  # argv tail that runs one test file, `{name}` substituted
    test_glob: str
    test_def: re.Pattern[str]
    hidden_name: str


SUITES = {
    "python": Suite(".", tuple(UNITTEST), "-p {name}", "*.py", re.compile(r"^\s*def test_", re.M), "hidden_behavior_test.py"),
    # node --test discovers **/*.test.js under the root; node_modules is skipped.
    "node": Suite("web", ("node", "--test"), "tests/{name}", "*.test.js", re.compile(r"^\s*(?:test|it)\(", re.M), "hidden_behavior.test.js"),
}


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    value: float | None = None


@dataclass(frozen=True)
class Context:
    project: Path
    reference: Path
    spec: Spec


def _text(spec: Spec, key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str):
        raise ValueError(f"check spec needs a string {key!r}; got {spec!r}")
    return value


def _run(command: list[str], cwd: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {"PATH": os.environ.get("PATH", ""), **(extra_env or {})}
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=60, check=False)  # noqa: S603  # nosec B603 -- fixed argv


def _suite(spec: Spec) -> Suite:
    name = spec.get("suite", "python")
    if not isinstance(name, str) or name not in SUITES:
        raise ValueError(f"check spec 'suite' must be one of {sorted(SUITES)}; got {spec!r}")
    return SUITES[name]


def run_suite(project: Path, suite: Suite = SUITES["python"]) -> subprocess.CompletedProcess[str]:
    """The project's own tests, run the way an agent would run them (unittest discovery, node --test)."""
    return _run(list(suite.command), project / suite.root)


@contextmanager
def scratch_copy(project: Path) -> Generator[Path, None, None]:
    """Disposable copy of `project`, so a check can swap files without touching the evidence."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp, "work")
        shutil.copytree(project, work, ignore=shutil.ignore_patterns(".claude", "__pycache__", ".atif-export.json"))
        yield work


def count_tests(root: Path, suite: Suite = SUITES["python"]) -> int:
    tests = root / suite.root / "tests"
    return sum(len(suite.test_def.findall(path.read_text())) for path in tests.rglob(suite.test_glob))


def finder_findings(skill: str, script: str, target: Path) -> list[dict[str, object]]:
    """JSON-lines findings of a find-* script on `target`; empty when nothing is found."""
    # uv run: the script's PEP 723 header brings tree-sitter for non-Python targets; HOME locates uv's cache.
    command = ["uv", "run", "--quiet", str(REPO / "skills" / skill / "scripts" / script), str(target)]
    done = _run(command, REPO, {"HOME": os.environ.get("HOME", "")})
    if done.returncode not in (0, 1):
        raise ValueError(f"{script} exited {done.returncode} on {str(target)!r}: {done.stderr[-200:]!r}")
    return [json.loads(line) for line in done.stdout.splitlines() if line.strip()]


def _branches(target: Path) -> int:
    findings = finder_findings("find-nested-branches", "find_nested_branches.py", target)
    return sum(int(str(f["elses"])) + int(str(f["elifs"])) for f in findings)


def suite_passes(ctx: Context) -> CheckResult:
    return CheckResult(run_suite(ctx.project, _suite(ctx.spec)).returncode == 0)


def tests_added(ctx: Context) -> CheckResult:
    suite = _suite(ctx.spec)
    delta = count_tests(ctx.project, suite) - count_tests(ctx.reference, suite)
    return CheckResult(delta >= 1, delta)


def hidden_passes(ctx: Context) -> CheckResult:
    """Copy a held-back behavior test into the project and run it; the agent never saw it."""
    suite = _suite(ctx.spec)
    with scratch_copy(ctx.project) as work:
        shutil.copy(HERE / _text(ctx.spec, "file"), work / suite.root / "tests" / suite.hidden_name)
        done = _run([*suite.command, *suite.only.format(name=suite.hidden_name).split()], work / suite.root)
    return CheckResult(done.returncode == 0)


def tests_fail_on_original(ctx: Context) -> CheckResult:
    """The agent's tests must fail, not on an import error, once the fixed files are put back to the bug."""
    files = ctx.spec.get("files")
    if not isinstance(files, list):
        raise ValueError(f"check spec needs a list 'files'; got {ctx.spec!r}")
    with scratch_copy(ctx.project) as work:
        for name in cast("list[str]", files):
            shutil.copy(ctx.reference / name, work / name)
        done = run_suite(work, _suite(ctx.spec))
    return CheckResult(done.returncode != 0 and not IMPORT_FAILURE.search(done.stderr + done.stdout))


def branching_not_increased(ctx: Context) -> CheckResult:
    """else/elif count in one file must not grow; value is after minus before (negative is better)."""
    path = _text(ctx.spec, "path")
    if not (ctx.project / path).exists():
        return CheckResult(False)
    delta = _branches(ctx.project / path) - _branches(ctx.reference / path)
    return CheckResult(delta <= 0, delta)


def no_tautologies(ctx: Context) -> CheckResult:
    count = len(finder_findings("find-tautological-assertions", "find_tautological_assertions.py", ctx.project / _text(ctx.spec, "path")))
    return CheckResult(count == 0, count)


def no_swallowed_errors(ctx: Context) -> CheckResult:
    """Exception handlers that discard their error (find-swallowed-errors) in one file; value is the count."""
    target = ctx.project / _text(ctx.spec, "path")
    if not target.exists():
        return CheckResult(False)
    count = len(finder_findings("find-swallowed-errors", "find_swallowed_errors.py", target))
    return CheckResult(count == 0, count)


def mutants_killed(ctx: Context) -> CheckResult:
    """How many injected one-line bugs the agent's tests catch; passes at spec['min']."""
    target, mutants, minimum = _text(ctx.spec, "file"), ctx.spec.get("mutants"), ctx.spec.get("min")
    if not isinstance(mutants, list) or not isinstance(minimum, int):
        raise ValueError(f"check spec needs a list 'mutants' and an int 'min'; got {ctx.spec!r}")
    original, suite = (ctx.reference / target).read_text(), _suite(ctx.spec)
    killed = 0
    with scratch_copy(ctx.project) as work:
        for old, new in cast("list[list[str]]", mutants):
            (work / target).write_text(original.replace(old, new, 1))
            killed += run_suite(work, suite).returncode != 0
        (work / target).write_text(original)
        if run_suite(work, suite).returncode != 0:
            return CheckResult(False, 0)
    return CheckResult(killed >= minimum, killed)


CHECKS: dict[str, Callable[[Context], CheckResult]] = {
    "suite_passes": suite_passes,
    "tests_added": tests_added,
    "hidden_passes": hidden_passes,
    "tests_fail_on_original": tests_fail_on_original,
    "branching_not_increased": branching_not_increased,
    "no_tautologies": no_tautologies,
    "no_swallowed_errors": no_swallowed_errors,
    "mutants_killed": mutants_killed,
}


def run_check(spec: Spec, project: Path, reference: Path) -> CheckResult:
    """Run the check named by spec['name']; an unknown name is a task-file bug and raises."""
    name = _text(spec, "name")
    if name not in CHECKS:
        raise ValueError(f"unknown check {name!r}; expected one of {sorted(CHECKS)}")
    return CHECKS[name](Context(project, reference, spec))
