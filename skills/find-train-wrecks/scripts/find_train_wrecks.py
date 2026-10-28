#!/usr/bin/env python3
"""Report expressions that reach through three or more links — Law of Demeter train wrecks.

Source is parsed with ast, never executed. Run with --help for usage and exit codes.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_MIN_HOPS = 3
_RECEIVERS = ("self", "cls")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    expression: str
    hops: int


def _chain_length(node: ast.AST) -> int:
    """Reaches in `node`'s access chain: attribute/subscript hops past the base name."""
    length = 0
    while True:
        if isinstance(node, ast.Call):
            node = node.func
        elif isinstance(node, (ast.Attribute, ast.Subscript)):
            length += 1
            node = node.value
        else:
            if isinstance(node, ast.Name) and node.id in _RECEIVERS:
                length -= 1
            return length


def find_wrecks(source: str, path: str) -> list[Finding]:
    """Maximal access chains in `source` with at least three reaches.

    >>> find_wrecks("x = a.b.c.d", "m.py")[0].hops
    3
    """
    tree = ast.parse(source, filename=path)
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Attribute, ast.Subscript)):
            continue
        parent = parents.get(id(node))
        continued = isinstance(parent, (ast.Attribute, ast.Subscript)) and parent.value is node
        continued |= isinstance(parent, ast.Call) and parent.func is node
        hops = _chain_length(node)
        if not continued and hops >= _MIN_HOPS:
            findings.append(Finding(path, node.lineno, ast.unparse(node), hops))
    return findings


def _python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise FileNotFoundError(f"{str(target)!r} is not a file or directory; expected a .py file or a directory")
    return sorted(p for p in target.rglob("*.py") if not any(part.startswith(".") for part in p.relative_to(target).parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_train_wrecks.py",
        description="Print one JSON object per train-wreck chain: path, line, expression, hops.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, syntax error, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH", help=".py file, or directory searched recursively")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        files = [f for arg in args.paths for f in _python_files(Path(arg))]
        findings = [f for file in files for f in find_wrecks(file.read_text(), str(file))]
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
