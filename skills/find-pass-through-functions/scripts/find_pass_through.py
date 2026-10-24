#!/usr/bin/env python3
"""Report pass-through functions: bodies that only forward their own parameters to another call.

Source is parsed with ast, never executed. Run with --help for usage and exit codes.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ArgShape = tuple[str, ...]
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_RECEIVERS = ("self", "cls")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    name: str
    callee: str


def _param_shape(args: ast.arguments) -> list[ArgShape]:
    positional = [a.arg for a in args.posonlyargs + args.args]
    if positional and positional[0] in _RECEIVERS:
        positional = positional[1:]
    shape: list[ArgShape] = [("pos", n) for n in positional]
    if args.vararg:
        shape.append(("star", args.vararg.arg))
    shape += [("kw", a.arg, a.arg) for a in args.kwonlyargs]
    if args.kwarg:
        shape.append(("dstar", args.kwarg.arg))
    return shape


def _call_shape(call: ast.Call) -> list[ArgShape]:
    shape: list[ArgShape] = []
    for arg in call.args:
        inner = arg.value if isinstance(arg, ast.Starred) else arg
        kind = "star" if isinstance(arg, ast.Starred) else "pos"
        shape.append((kind, inner.id) if isinstance(inner, ast.Name) else ("other",))
    for kw in call.keywords:
        if not isinstance(kw.value, ast.Name):
            shape.append(("other",))
        elif kw.arg is None:
            shape.append(("dstar", kw.value.id))
        else:
            shape.append(("kw", kw.arg, kw.value.id))
    return shape


def _single_call(fn: FunctionNode) -> ast.Call | None:
    body = fn.body
    first = body[0] if body else None
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], (ast.Return, ast.Expr)):
        return None
    value = body[0].value
    value = value.value if isinstance(value, ast.Await) else value
    return value if isinstance(value, ast.Call) else None


def _is_super_call(call: ast.Call) -> bool:
    receiver = call.func.value if isinstance(call.func, ast.Attribute) else None
    return isinstance(receiver, ast.Call) and ast.unparse(receiver.func) == "super"


def _pass_through_callee(fn: FunctionNode) -> str | None:
    """Callee name when `fn` only forwards its own parameters unchanged; decorated, super() and zero-arg are skipped."""
    call = _single_call(fn)
    if fn.decorator_list or call is None or _is_super_call(call):
        return None
    shape = _param_shape(fn.args)
    return ast.unparse(call.func) if shape and shape == _call_shape(call) else None


def find_pass_throughs(source: str, path: str) -> list[Finding]:
    """Pass-through functions in `source`.

    >>> find_pass_throughs("def get(id):\\n    return repo.get(id)", "m.py")[0].callee
    'repo.get'
    """
    functions = [n for n in ast.walk(ast.parse(source, filename=path)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return [Finding(path, fn.lineno, fn.name, callee) for fn in functions if (callee := _pass_through_callee(fn))]


def _python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise FileNotFoundError(f"{str(target)!r} is not a file or directory; expected a .py file or a directory")
    return sorted(p for p in target.rglob("*.py") if not any(part.startswith(".") for part in p.parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_pass_through.py",
        description="Print one JSON object per pass-through function: path, line, name, callee.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, syntax error, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH", help=".py file, or directory searched recursively")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        files = [f for arg in args.paths for f in _python_files(Path(arg))]
        findings = [f for file in files for f in find_pass_throughs(file.read_text(), str(file))]
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
