#!/usr/bin/env python3
"""Report functions whose control flow nests or uses else/elif — flat-methods smells.

Source is parsed with ast, never executed. Run with --help for usage and exit codes.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_DECISION = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Match)
_MAX_DEPTH = 1


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    name: str
    elses: int
    elifs: int
    depth: int


def _if_counts(fn: FunctionNode) -> tuple[int, int]:
    elses = elifs = 0
    for node in ast.walk(fn):
        if not isinstance(node, ast.If) or not node.orelse:
            continue
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            elifs += 1
        else:
            elses += 1
    return elses, elifs


def _depth(node: ast.AST, level: int) -> int:
    best = level
    for child in ast.iter_child_nodes(node):
        next_level = level + 1 if isinstance(child, _DECISION) else level
        best = max(best, _depth(child, next_level))
    return best


def find_nested(source: str, path: str) -> list[Finding]:
    """Functions in `source` with else/elif branches or decision nesting deeper than one level.

    >>> find_nested("def f(x):\\n    if x:\\n        a()\\n    else:\\n        b()", "m.py")[0].elses
    1
    """
    functions = [n for n in ast.walk(ast.parse(source, filename=path)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    findings = []
    for fn in functions:
        elses, elifs = _if_counts(fn)
        depth = _depth(fn, 0)
        if elses + elifs or depth > _MAX_DEPTH:
            findings.append(Finding(path, fn.lineno, fn.name, elses, elifs, depth))
    return findings


def _python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise FileNotFoundError(f"{str(target)!r} is not a file or directory; expected a .py file or a directory")
    return sorted(p for p in target.rglob("*.py") if not any(part.startswith(".") for part in p.relative_to(target).parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_nested_branches.py",
        description="Print one JSON object per function using else/elif or nesting decisions: path, line, name, elses, elifs, depth.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, syntax error, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH", help=".py file, or directory searched recursively")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        files = [f for arg in args.paths for f in _python_files(Path(arg))]
        findings = [f for file in files for f in find_nested(file.read_text(), str(file))]
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
