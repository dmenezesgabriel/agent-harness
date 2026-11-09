#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["tree-sitter-language-pack==1.22.1"]
# [tool.uv]
# exclude-newer = "2026-11-01T00:00:00Z"
# ///
"""Report exception handlers that swallow errors — fix-root-causes hiding places.

A handler swallows when its body produces no observable response: it is empty
(pass/ellipsis/docstring only, or a bare block) or it only returns, discarding
the error into a value the caller cannot distinguish. Promise `.catch(cb)`
handlers are reported under the same rule.

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node

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
_CATCH = {"ts": "catch_clause", "java": "catch_clause", "kotlin": "catch_block"}
_BODY = {"ts": "statement_block", "java": "block", "kotlin": "statements"}
_NO_INVOCATION = {"call_expression", "await_expression", "new_expression"}


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    name: str
    handler: str
    body: str


def _enclosing_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return "<module>"


def _handler_body_kind(handler: ast.ExceptHandler) -> str | None:
    stmts = [s for s in handler.body
             if not isinstance(s, ast.Pass)
             and not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    if not stmts:
        return "empty"
    if all(isinstance(s, ast.Return) for s in stmts):
        return "return"
    return None


def find_swallowed(source: str, path: str) -> list[Finding]:
    """Exception handlers in Python `source` whose body is empty or only returns.

    >>> f = find_swallowed("def f():\\n    try:\\n        a()\\n    except Exception:\\n        pass", "m.py")
    >>> (f[0].name, f[0].body)
    ('f', 'empty')
    """
    tree = ast.parse(source, filename=path)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Try, ast.TryStar)):
            continue
        for handler in node.handlers:
            kind = _handler_body_kind(handler)
            if kind is not None:
                findings.append(Finding(path, handler.lineno, _enclosing_name(handler, parents), "except", kind))
    return findings


def node_text(node: Node) -> str:
    """Decoded source text of `node` ('' when tree-sitter reports no text)."""
    text = node.text
    return text.decode() if text is not None else ""


def _is_comment(node: Node) -> bool:
    return node.type == "comment" or node.type.endswith("_comment")


def _is_return(node: Node, family: str) -> bool:
    if node.type == "return_statement":
        return True
    return family == "kotlin" and node.type == "jump_expression" and node_text(node).lstrip().startswith("return")


def _block_kind(block: Node | None, family: str) -> str | None:
    """'empty' when `block` has no effective statements, 'return' when all are returns."""
    stmts = [] if block is None else [c for c in block.named_children if not _is_comment(c)]
    if not stmts:
        return "empty"
    if all(_is_return(s, family) for s in stmts):
        return "return"
    return None


def _has_invocation(node: Node) -> bool:
    if node.type in _NO_INVOCATION:
        return True
    return any(_has_invocation(child) for child in node.children)


def _catch_body(handler: Node, family: str) -> Node | None:
    body_type = _BODY[family]
    for child in handler.named_children:
        if child.type == body_type:
            return child
    return None


def _function_name(node: Node, family: str) -> str:
    if family == "kotlin":
        return next((node_text(c) for c in node.named_children if c.type == "simple_identifier"), "<anonymous>")
    name = node.child_by_field_name("name")
    if name is not None:
        return node_text(name)
    parent = node.parent
    if parent is not None and parent.type in {"variable_declarator", "pair"}:
        field = "key" if parent.type == "pair" else "name"
        named = parent.child_by_field_name(field)
        if named is not None:
            return node_text(named)
    return "<anonymous>"


def _enclosing(node: Node, family: str) -> str:
    while node.parent is not None:
        node = node.parent
        if node.type in _FUNCTIONS[family]:
            return _function_name(node, family)
    return "<module>"


def _catch_findings(node: Node, path: str, family: str) -> list[Finding]:
    body = _catch_body(node, family)
    kind = _block_kind(body, family)
    if kind is None:
        return []
    return [Finding(path, node.start_point[0] + 1, _enclosing(node, family), "catch", kind)]


def _promise_findings(call: Node, path: str) -> list[Finding]:
    """Flag `.catch(cb)` where `cb` swallows: empty/return-only block or a value body."""
    function = call.child_by_field_name("function")
    if function is None or function.type != "member_expression":
        return []
    prop = function.child_by_field_name("property")
    if prop is None or node_text(prop) != "catch":
        return []
    args = call.child_by_field_name("arguments")
    callback = next((c for c in (args.named_children if args else [])
                     if c.type in {"arrow_function", "function", "function_expression"}), None)
    if callback is None:
        return []
    body = callback.child_by_field_name("body")
    if body is None:
        return []
    kind = _block_kind(body, "ts") if body.type == "statement_block" else None if _has_invocation(body) else "return"
    if kind is None:
        return []
    return [Finding(path, call.start_point[0] + 1, _enclosing(call, "ts"), ".catch()", kind)]


def find_swallowed_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Exception handlers in TypeScript/JavaScript/Java/Kotlin `source` that swallow errors.

    >>> f = find_swallowed_tree(b"function f(){ try { a() } catch (e) {} }", "m.ts", "typescript")
    >>> (f[0].name, f[0].handler, f[0].body)
    ('f', 'catch', 'empty')
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not installed; run via `uv run scripts/find_swallowed_errors.py` "
            "(PEP 723 dependencies are declared in this script)"
        ) from error
    tree = get_parser(grammar).parse(source)
    if tree.root_node.has_error:
        raise SyntaxError(f"{path!r}: could not parse as {grammar}; expected valid source")
    family = _FAMILY[grammar]
    findings: list[Finding] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == _CATCH[family]:
            findings += _catch_findings(node, path, family)
        if family == "ts" and node.type == "call_expression":
            findings += _promise_findings(node, path)
        stack.extend(node.children)
    return findings


def source_files(target: Path) -> list[Path]:
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
        prog="find_swallowed_errors.py",
        description="Print one JSON object per exception handler that swallows its error: path, line, name, handler, body.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, unsupported file, no file parsed, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH",
                        help="source file, or directory searched recursively (.py, .ts, .tsx, .js, .jsx, .java, .kt, .kts)")
    return parser.parse_args(argv)


def _scan_file(file: Path) -> tuple[int, list[Finding]]:
    """(parsed-count, findings) for `file`: warn-and-skip parse errors, let MissingTreeSitter through."""
    try:
        return 1, _find_in_file(file)
    except (SyntaxError, UnicodeDecodeError) as error:
        print(f"warning: {error}; skipped", file=sys.stderr)
        return 0, []


def _find_in_file(file: Path) -> list[Finding]:
    if file.suffix == ".py":
        return find_swallowed(file.read_text(), str(file))
    return find_swallowed_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    paths: list[str] = args.paths
    try:
        files = [f for arg in paths for f in source_files(Path(arg))]
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    findings: list[Finding] = []
    parsed = 0
    for file in files:
        try:
            parsed_file, found = _scan_file(file)
        except MissingTreeSitter as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        parsed += parsed_file
        findings += found
    if files and not parsed:
        return 2
    for finding in findings:
        print(json.dumps(asdict(finding)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
