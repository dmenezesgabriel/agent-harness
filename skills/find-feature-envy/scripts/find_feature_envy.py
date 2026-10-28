#!/usr/bin/env python3
"""Report functions that read several attributes of one foreign value — feature envy.

Source is parsed with ast, never executed. Run with --help for usage and exit codes.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_MIN_ATTRS = 3
_RECEIVERS = ("self", "cls")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    name: str
    target: str
    attrs: list[str] = field(default_factory=list)


def _param_names(args: ast.arguments) -> set[str]:
    names = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs} - set(_RECEIVERS)
    names |= {a.arg for a in (args.vararg, args.kwarg) if a}
    return names


def find_envy(source: str, path: str) -> list[Finding]:
    """Functions in `source` reading three or more distinct attributes of one parameter.

    >>> find_envy("def f(u):\\n    return u.a + u.b + u.c", "m.py")[0].target
    'u'
    """
    functions = [n for n in ast.walk(ast.parse(source, filename=path)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    findings = []
    for fn in functions:
        params = _param_names(fn.args)
        hits: dict[str, set[str]] = {}
        for node in ast.walk(fn):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in params:
                hits.setdefault(node.value.id, set()).add(node.attr)
        for base, attrs in sorted(hits.items()):
            if len(attrs) >= _MIN_ATTRS:
                findings.append(Finding(path, fn.lineno, fn.name, base, sorted(attrs)))
    return findings


def _python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise FileNotFoundError(f"{str(target)!r} is not a file or directory; expected a .py file or a directory")
    return sorted(p for p in target.rglob("*.py") if not any(part.startswith(".") for part in p.relative_to(target).parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_feature_envy.py",
        description="Print one JSON object per envious function: path, line, name, target, attrs.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, syntax error, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH", help=".py file, or directory searched recursively")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        files = [f for arg in args.paths for f in _python_files(Path(arg))]
        findings = [f for file in files for f in find_envy(file.read_text(), str(file))]
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
