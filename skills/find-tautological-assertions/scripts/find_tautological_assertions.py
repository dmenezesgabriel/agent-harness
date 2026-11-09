#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["tree-sitter-language-pack==1.22.1"]
# [tool.uv]
# exclude-newer = "2026-11-01T00:00:00Z"
# ///
"""Report assertions that cannot fail — test-behavior smells.

An assertion is tautological when it compares an expression to itself
(`assertEquals(x, x)`, `expect(x).toBe(x)`, `assert x == x`) or asserts a
constant that makes it always true (`assertTrue(true)`, `assert True`).

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
_EXPECT_SAME = {"toBe", "toEqual", "toStrictEqual"}
_EXPECT_TRUTHY = {"toBeTruthy", "toBeTrue"}
_ASSERT_SAME = {"equal", "strictEqual", "deepEqual", "deepStrictEqual", "equals",
                "assertEquals", "assertSame", "assertArrayEquals", "assertIterableEquals", "assertContentEquals"}
_BINARY_SAME = {"==", "==="}
_BINARY_DIFF = {"!=", "!=="}


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    name: str
    assertion: str
    kind: str


def _enclosing_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return "<module>"


def _same_operands(test: ast.expr) -> bool:
    """True when `test` is `x == x` or `x is x` — every operand identical."""
    if not isinstance(test, ast.Compare) or not all(isinstance(op, (ast.Eq, ast.Is)) for op in test.ops):
        return False
    operands = [test.left, *test.comparators]
    return len({ast.unparse(operand) for operand in operands}) == 1


def _assert_call_kind(call: ast.Call) -> str | None:
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else "")
    if not name.startswith("assert"):
        return None
    if len(call.args) >= 2 and ast.unparse(call.args[0]) == ast.unparse(call.args[1]):
        return "same-operands"
    if call.args and _same_operands(call.args[0]):
        return "same-operands"
    if call.args and isinstance(call.args[0], ast.Constant):
        if name in {"assertTrue", "assert_"} and call.args[0].value is True:
            return "always-true"
        if name == "assertFalse" and call.args[0].value is False:
            return "always-true"
    return None


def _snippet(node: ast.AST, source: str) -> str:
    segment = ast.get_source_segment(source, node) or ast.unparse(node)
    return " ".join(segment.split())[:80]


def find_tautologies(source: str, path: str) -> list[Finding]:
    """Assertions in Python `source` that compare an expression to itself or assert a constant.

    >>> f = find_tautologies("def t():\\n    assert x == x", "t.py")
    >>> (f[0].name, f[0].kind)
    ('t', 'same-operands')
    """
    tree = ast.parse(source, filename=path)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    findings: list[Finding] = []
    for node in ast.walk(tree):
        kind = None
        if isinstance(node, ast.Assert):
            if _same_operands(node.test):
                kind = "same-operands"
            elif isinstance(node.test, ast.Constant) and node.test.value:
                kind = "always-true"
        elif isinstance(node, ast.Call):
            kind = _assert_call_kind(node)
        else:
            continue
        if kind is not None:
            findings.append(Finding(path, node.lineno, _enclosing_name(node, parents), _snippet(node, source), kind))
    return findings


def node_text(node: Node) -> str:
    """Decoded source text of `node` ('' when tree-sitter reports no text)."""
    text = node.text
    return text.decode() if text is not None else ""


def _norm(node: Node) -> str:
    text = node_text(node)
    while text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    return "".join(text.split())


def _unwrap(node: Node) -> Node:
    while node.type in {"parenthesized_expression", "value_argument"} and node.named_children:
        node = node.named_children[0]
    return node


def _binary_same(node: Node, operators: set[str]) -> bool:
    if node.type not in {"binary_expression", "equality_expression"} or len(node.named_children) != 2:
        return False
    op = next((c for c in node.children if not c.is_named and c.type in operators | _BINARY_DIFF), None)
    if op is None or op.type not in operators:
        return False
    left, right = node.named_children
    return _norm(left) == _norm(right)


def _call_args(node: Node, arg_node: str) -> list[Node]:
    args = node.child_by_field_name("arguments")
    if args is not None:
        return args.named_children
    stack = list(node.named_children)
    while stack:
        candidate = stack.pop()
        if candidate.type == arg_node:
            return candidate.named_children
        stack.extend(candidate.named_children)
    return []


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


def _truth_kind(first: Node, literal: str, operators: set[str]) -> str | None:
    """'always-true' when `first` is the literal itself, 'same-operands' when it compares a value to itself."""
    if _norm(first) == literal:
        return "always-true"
    return "same-operands" if _binary_same(first, operators) else None


def _ts_expect_kind(expect_call: Node, prop: str, args: list[Node]) -> str | None:
    """expect(x).toBe(x) or expect(true).toBeTruthy()."""
    expect_fn = expect_call.child_by_field_name("function")
    expect_args = _call_args(expect_call, "arguments")
    if expect_fn is None or node_text(expect_fn) != "expect" or not expect_args:
        return None
    subject = _norm(_unwrap(expect_args[0]))
    if prop in _EXPECT_SAME and args and subject == _norm(_unwrap(args[0])):
        return "same-operands"
    return "always-true" if prop in _EXPECT_TRUTHY and subject == "true" else None


def _ts_assert_member_kind(prop: str, args: list[Node]) -> str | None:
    """assert.equal(x, x), assert.ok(true), assert.ok(x === x)."""
    first = _unwrap(args[0])
    if prop in _ASSERT_SAME and len(args) >= 2 and _norm(first) == _norm(_unwrap(args[1])):
        return "same-operands"
    if prop == "ok" and _norm(first) == "true":
        return "always-true"
    return "same-operands" if prop in _ASSERT_SAME | {"ok"} and _binary_same(first, _BINARY_SAME) else None


def _ts_method_kind(function: Node, args: list[Node]) -> str | None:
    prop = node_text(function.child_by_field_name("property") or function)
    obj = function.child_by_field_name("object")
    if obj is None:
        return None
    if obj.type == "call_expression":
        return _ts_expect_kind(obj, prop, args)
    return _ts_assert_member_kind(prop, args) if node_text(obj) == "assert" and args else None


def _ts_member_kind(call: Node) -> str | None:
    """expect(x).toBe(x), assert.equal(x,x), assert.ok(true), bare assert(true|x==x)."""
    function = call.child_by_field_name("function")
    if function is None:
        return None
    args = _call_args(call, "arguments")
    if function.type == "member_expression":
        return _ts_method_kind(function, args)
    if function.type == "identifier" and node_text(function) in {"assert", "assertTrue", "assert_"} and args:
        return _truth_kind(_unwrap(args[0]), "true", _BINARY_SAME)
    return None


# Java truth assertions: the literal that makes them hollow, and the self-comparison operators.
_JAVA_TRUTH = {"assertTrue": ("true", {"=="}), "assertFalse": ("false", {"!="})}


def _java_assert_statement_kind(node: Node) -> str | None:
    expr = _unwrap(node.named_children[0]) if node.named_children else None
    return _truth_kind(expr, "true", {"=="}) if expr is not None else None


def _java_kind(node: Node) -> str | None:
    if node.type == "assert_statement":
        return _java_assert_statement_kind(node)
    if node.type != "method_invocation":
        return None
    name_node = node.child_by_field_name("name")
    name = node_text(name_node) if name_node is not None else ""
    if name not in _ASSERT_SAME | _JAVA_TRUTH.keys():
        return None
    args_node = next((c for c in node.named_children if c.type == "argument_list"), None)
    args = args_node.named_children if args_node is not None else []
    if len(args) >= 2 and name in _ASSERT_SAME and _norm(_unwrap(args[0])) == _norm(_unwrap(args[1])):
        return "same-operands"
    if not args or name not in _JAVA_TRUTH:
        return None
    literal, operators = _JAVA_TRUTH[name]
    return _truth_kind(_unwrap(args[0]), literal, operators)


def _kotlin_kind(node: Node) -> str | None:
    if node.type != "call_expression" or not node.named_children or node.named_children[0].type != "simple_identifier":
        return None
    name = node_text(node.named_children[0])
    if name not in _ASSERT_SAME | {"assertTrue", "assertFalse", "assert"}:
        return None
    args = _call_args(node, "value_arguments")
    values = [_unwrap(a) for a in args]
    if len(values) >= 2 and name in _ASSERT_SAME and _norm(values[0]) == _norm(values[1]):
        return "same-operands"
    if values:
        first = values[0]
        if name in {"assertTrue", "assert"} and (_norm(first) == "true" or _binary_same(first, _BINARY_SAME)):
            return "always-true" if _norm(first) == "true" else "same-operands"
        if name == "assertFalse" and (_norm(first) == "false" or _binary_same(first, {"!=", "!=="})):
            return "always-true" if _norm(first) == "false" else "same-operands"
    return None


def _tree_kind(node: Node, family: str) -> str | None:
    if family == "ts":
        return _ts_member_kind(node) if node.type == "call_expression" else None
    if family == "java":
        return _java_kind(node)
    return _kotlin_kind(node)


def find_tautologies_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Assertions in TypeScript/JavaScript/Java/Kotlin `source` that cannot fail.

    >>> f = find_tautologies_tree(b"expect(x).toBe(x)", "t.ts", "typescript")
    >>> (f[0].name, f[0].kind)
    ('<module>', 'same-operands')
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not importable; run via `uv run scripts/find_tautological_assertions.py` "
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
        kind = _tree_kind(node, family)
        if kind is not None:
            assertion = " ".join(node_text(node).split())[:80]
            findings.append(Finding(path, node.start_point[0] + 1, _enclosing(node, family), assertion, kind))
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
        prog="find_tautological_assertions.py",
        description="Print one JSON object per assertion that cannot fail: path, line, name, assertion, kind.",
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
        return find_tautologies(file.read_text(), str(file))
    return find_tautologies_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


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
