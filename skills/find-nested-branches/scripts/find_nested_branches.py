#!/usr/bin/env python3
# /// script
# dependencies = ["tree-sitter-language-pack"]
# ///
"""Report functions whose control flow nests or uses else/elif — flat-methods smells.

Python is parsed with ast; TypeScript/JavaScript, Java, and Kotlin with tree-sitter
(run those via uv, deps declared above). Source is parsed, never executed.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_DECISION = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Match)
_MAX_DEPTH = 1
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
_IF = {"ts": {"if_statement"}, "java": {"if_statement"}, "kotlin": {"if_expression"}}
# Kotlin `if` is an expression too; value-position ifs (ternaries) are excluded like Python's IfExp.
_STATEMENT_PARENTS = {"statements", "control_structure_body"}
_DECISIONS = {
    "ts": {"if_statement", "for_statement", "for_in_statement", "while_statement",
           "do_statement", "switch_statement"},
    "java": {"if_statement", "for_statement", "enhanced_for_statement", "while_statement",
             "do_statement", "switch_expression", "switch_statement"},
    "kotlin": {"for_statement", "while_statement", "do_while_statement", "when_expression"},
}


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


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
    """Functions in Python `source` with else/elif branches or decision nesting deeper than one level.

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


def _is_branchy(node: Any, parent_type: str, family: str) -> bool:
    if node.type in _IF[family]:
        return family != "kotlin" or parent_type in _STATEMENT_PARENTS
    return node.type in _DECISIONS[family]


def _alternative_kind(node: Any, family: str) -> str | None:
    """'elif', 'else', or None for an if node's else branch."""
    alternative = node.child_by_field_name("alternative")
    if alternative is None:
        return None
    if family == "ts":
        inner = alternative.named_children[0] if alternative.named_children else None
        return "elif" if inner is not None and inner.type == "if_statement" else "else"
    if family == "java":
        return "elif" if alternative.type == "if_statement" else "else"
    inner = alternative.named_children[0] if alternative.named_children else None
    return "elif" if inner is not None and inner.type == "if_expression" else "else"


def _tree_if_counts(fn: Any, family: str) -> tuple[int, int]:
    elses = elifs = 0
    stack = [(child, fn.type) for child in fn.children]
    while stack:
        node, parent_type = stack.pop()
        if node.type in _IF[family] and _is_branchy(node, parent_type, family):
            kind = _alternative_kind(node, family)
            elses += kind == "else"
            elifs += kind == "elif"
        stack.extend((child, node.type) for child in node.children)
    return elses, elifs


def _tree_depth(node: Any, family: str) -> int:
    best = 0
    for child in node.children:
        next_level = 1 if _is_branchy(child, node.type, family) else 0
        best = max(best, next_level + _tree_depth(child, family))
    return best


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


def find_nested_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Functions in TypeScript/JavaScript/Java/Kotlin `source` with else/elif or nesting deeper than one level.

    >>> find_nested_tree(b"function f(x){ if (x) { a() } else { b() } }", "m.ts", "typescript")[0].elses
    1
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not installed; run via `uv run scripts/find_nested_branches.py` "
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
        elses, elifs = _tree_if_counts(fn, family)
        depth = _tree_depth(fn, family)
        if elses + elifs or depth > _MAX_DEPTH:
            findings.append(Finding(path, fn.start_point[0] + 1, _function_name(fn, family), elses, elifs, depth))
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
        prog="find_nested_branches.py",
        description="Print one JSON object per function using else/elif or nesting decisions: path, line, name, elses, elifs, depth.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, unsupported file, no file parsed, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH",
                        help="source file, or directory searched recursively (.py, .ts, .tsx, .js, .jsx, .java, .kt, .kts)")
    return parser.parse_args(argv)


def _find_in_file(file: Path) -> list[Finding]:
    if file.suffix == ".py":
        return find_nested(file.read_text(), str(file))
    return find_nested_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


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
