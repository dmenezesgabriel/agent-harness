#!/usr/bin/env python3
# /// script
# dependencies = ["tree-sitter-language-pack"]
# ///
"""Report functions that read several attributes of one foreign value — feature envy.

Python is parsed with ast; TypeScript/JavaScript, Java, and Kotlin with tree-sitter
(run those via uv, deps declared above). Source is parsed, never executed.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_MIN_ATTRS = 3
_RECEIVERS = ("self", "cls")
_LANGUAGES = {
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".tsx": "tsx", ".js": "tsx", ".jsx": "tsx", ".mjs": "tsx", ".cjs": "tsx",
    ".java": "java",
    ".kt": "kotlin", ".kts": "kotlin",
}
_FAMILY = {"typescript": "ts", "tsx": "ts", "java": "java", "kotlin": "kotlin"}
_SKIP_DIRS = {"node_modules", "dist", "build", "target", "out", "vendor", "coverage", "__pycache__"}
_FUNCTIONS = {
    "ts": {"function_declaration", "function_expression", "generator_function_declaration",
           "generator_function", "method_definition", "arrow_function"},
    "java": {"method_declaration", "constructor_declaration"},
    "kotlin": {"function_declaration"},
}


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


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
    """Functions in Python `source` reading three or more distinct attributes of one parameter.

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


def _ts_params(fn: Any) -> set[str]:
    params = fn.child_by_field_name("parameters")
    if params is None:
        return set()
    names = set()
    for child in params.named_children:
        pattern = child.child_by_field_name("pattern") if child.type in {"required_parameter", "optional_parameter"} else None
        if pattern is not None and pattern.type == "identifier":
            names.add(pattern.text.decode())
    return names


def _ts_hits(fn: Any, params: set[str]) -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {}
    stack = [fn]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type != "member_expression":
            continue
        obj = node.child_by_field_name("object")
        prop = node.child_by_field_name("property")
        if obj is not None and obj.type == "identifier" and obj.text.decode() in params and prop is not None:
            hits.setdefault(obj.text.decode(), set()).add(prop.text.decode())
    return hits


def _java_params(fn: Any) -> set[str]:
    params = fn.child_by_field_name("parameters")
    if params is None:
        return set()
    names = set()
    for child in params.named_children:
        name = child.child_by_field_name("name") if child.type == "formal_parameter" else None
        if name is not None:
            names.add(name.text.decode())
    return names


def _java_hits(fn: Any, params: set[str]) -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {}
    stack = [fn]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type == "field_access":
            obj, attr = node.child_by_field_name("object"), node.child_by_field_name("field")
        elif node.type == "method_invocation":
            obj, attr = node.child_by_field_name("object"), node.child_by_field_name("name")
        else:
            continue
        if obj is not None and obj.type == "identifier" and obj.text.decode() in params and attr is not None:
            hits.setdefault(obj.text.decode(), set()).add(attr.text.decode())
    return hits


def _kotlin_params(fn: Any) -> set[str]:
    params = next((c for c in fn.children if c.type == "function_value_parameters"), None)
    if params is None:
        return set()
    names = set()
    for child in params.named_children:
        ident = next((c for c in child.named_children if c.type == "simple_identifier"), None) if child.type == "parameter" else None
        if ident is not None:
            names.add(ident.text.decode())
    return names


def _kotlin_hits(fn: Any, params: set[str]) -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {}
    stack = [fn]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type != "navigation_expression" or not node.children:
            continue
        receiver = node.children[0]
        suffix = next((c for c in node.children if c.type == "navigation_suffix"), None)
        ident = next((c for c in suffix.named_children if c.type == "simple_identifier"), None) if suffix is not None else None
        if receiver.type == "simple_identifier" and receiver.text.decode() in params and ident is not None:
            hits.setdefault(receiver.text.decode(), set()).add(ident.text.decode())
    return hits


_PARAMS = {"ts": _ts_params, "java": _java_params, "kotlin": _kotlin_params}
_HITS = {"ts": _ts_hits, "java": _java_hits, "kotlin": _kotlin_hits}


def _function_name(node: Any, family: str) -> str:
    if family == "kotlin":
        return next((c.text.decode() for c in node.named_children if c.type == "simple_identifier"), "<anonymous>")
    name = node.child_by_field_name("name")
    if name is not None:
        return name.text.decode()
    parent = node.parent
    if parent is not None and parent.type in {"variable_declarator", "pair"}:
        named = parent.child_by_field_name("name")
        if named is not None:
            return named.text.decode()
    return "<anonymous>"


def find_envy_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Functions in TypeScript/JavaScript/Java/Kotlin `source` reading three or more attributes of one parameter.

    >>> find_envy_tree(b"function f(u){ return u.a + u.b + u.c }", "m.ts", "typescript")[0].target
    'u'
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not installed; run via `uv run scripts/find_feature_envy.py` "
            "(PEP 723 dependencies are declared in this script)"
        ) from error
    tree = get_parser(grammar).parse(source)
    if tree.root_node.has_error:
        raise SyntaxError(f"{path!r}: could not parse as {grammar}; expected valid source")
    family = _FAMILY[grammar]
    functions = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in _FUNCTIONS[family]:
            functions.append(node)
        stack.extend(node.children)
    findings = []
    for fn in functions:
        params = _PARAMS[family](fn)
        if not params:
            continue
        for base, attrs in sorted(_HITS[family](fn, params).items()):
            if len(attrs) >= _MIN_ATTRS:
                findings.append(Finding(path, fn.start_point[0] + 1, _function_name(fn, family), base, sorted(attrs)))
    return findings


def _source_files(target: Path) -> list[Path]:
    if target.is_file():
        if target.suffix != ".py" and target.suffix not in _LANGUAGES:
            raise FileNotFoundError(
                f"{str(target)!r} has unsupported suffix {target.suffix!r}; expected .py/.ts/.tsx/.js/.jsx/.java/.kt/.kts")
        return [target]
    if not target.is_dir():
        raise FileNotFoundError(
            f"{str(target)!r} is not a file or directory; expected .py/.ts/.tsx/.js/.jsx/.java/.kt/.kts or a directory")
    return sorted(p for p in target.rglob("*")
                  if (p.suffix == ".py" or p.suffix in _LANGUAGES)
                  and not any(part.startswith(".") or part in _SKIP_DIRS for part in p.relative_to(target).parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_feature_envy.py",
        description="Print one JSON object per envious function: path, line, name, target, attrs.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, unsupported file, no file parsed, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH",
                        help="source file, or directory searched recursively (.py, .ts, .tsx, .js, .jsx, .java, .kt, .kts)")
    return parser.parse_args(argv)


def _find_in_file(file: Path) -> list[Finding]:
    if file.suffix == ".py":
        return find_envy(file.read_text(), str(file))
    return find_envy_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        files = [f for arg in args.paths for f in _source_files(Path(arg))]
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    findings = []
    parsed = 0
    for file in files:
        try:
            findings += _find_in_file(file)
            parsed += 1
        except MissingTreeSitter as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"warning: {error}; skipped", file=sys.stderr)
    if files and not parsed:
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
