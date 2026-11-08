#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["tree-sitter-language-pack==1.22.1"]
# [tool.uv]
# exclude-newer = "2026-11-01T00:00:00Z"
# ///
"""Report expressions that reach through three or more links — Law of Demeter train wrecks.

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

_MIN_HOPS = 3
_RECEIVERS = ("self", "cls")
# suffix -> tree-sitter grammar
_LANGUAGES = {
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".tsx": "tsx", ".js": "tsx", ".jsx": "tsx", ".mjs": "tsx", ".cjs": "tsx",
    ".java": "java",
    ".kt": "kotlin", ".kts": "kotlin",
}
# tree-sitter grammar -> language family used by _LINKS/_FREE_BASES
_FAMILY = {"typescript": "ts", "tsx": "ts", "java": "java", "kotlin": "kotlin"}
_SKIP_DIRS = {"node_modules", "dist", "build", "target", "out", "vendor", "coverage", "__pycache__"}
# language family -> {node type: (receiver field name or child index, hops added)}
_LINKS: dict[str, dict[str, tuple[str | int, int]]] = {
    "ts": {"member_expression": ("object", 1), "subscript_expression": ("object", 1),
           "call_expression": ("function", 0)},
    "java": {"field_access": ("object", 1), "method_invocation": ("object", 1),
             "array_access": ("array", 1)},
    "kotlin": {"navigation_expression": (0, 1), "indexing_expression": (0, 1),
               "call_expression": (0, 0)},
}
_FREE_BASES = {"ts": {"this"}, "java": {"this"}, "kotlin": {"this_expression"}}


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


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
    """Maximal access chains in Python `source` with at least three reaches.

    >>> find_wrecks("x = a.b.c.d", "m.py")[0].hops
    3
    """
    tree = ast.parse(source, filename=path)
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    findings: list[Finding] = []
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


def node_text(node: Node) -> str:
    """Decoded source text of `node` ('' when tree-sitter reports no text)."""
    text = node.text
    return text.decode() if text is not None else ""


def _receiver(node: Node, spec: tuple[str | int, int]) -> Node | None:
    field = spec[0]
    return node.children[field] if isinstance(field, int) and len(node.children) > field else (
        node.child_by_field_name(field) if isinstance(field, str) else None)


def _tree_hops(node: Node | None, links: dict[str, tuple[str | int, int]]) -> tuple[int, Node | None]:
    """(hops, base node) for the chain rooted at `node`; stops at the first non-link."""
    hops = 0
    while node is not None and node.type in links:
        receiver = _receiver(node, links[node.type])
        if receiver is None:
            break
        hops += links[node.type][1]
        node = receiver
    return hops, node


def _tree_parents(root: Node) -> dict[int, Node]:
    """Map stable tree-sitter node ids to parents; Python `id()` is unstable across accesses."""
    parents: dict[int, Node] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in node.children:
            parents[child.id] = node
            stack.append(child)
    return parents


def find_wrecks_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Maximal access chains in TypeScript/JavaScript/Java/Kotlin `source` with at least three reaches.

    >>> find_wrecks_tree(b"const x = a.b.c.d;", "m.ts", "typescript")[0].hops
    3
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not installed; run via `uv run scripts/find_train_wrecks.py` "
            "(PEP 723 dependencies are declared in this script)"
        ) from error
    tree = get_parser(grammar).parse(source)
    if tree.root_node.has_error:
        raise SyntaxError(f"{path!r}: could not parse as {grammar}; expected valid source")
    family = _FAMILY[grammar]
    links = _LINKS[family]
    parents = _tree_parents(tree.root_node)
    findings: list[Finding] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        spec = links.get(node.type)
        if spec is None or _receiver(node, spec) is None:
            continue
        parent = parents.get(node.id)
        continued = (parent is not None and parent.type in links
                     and _receiver(parent, links[parent.type]) == node)
        hops, base = _tree_hops(node, links)
        if base is not None and base.type in _FREE_BASES[family]:
            hops -= 1
        if not continued and hops >= _MIN_HOPS:
            findings.append(Finding(path, node.start_point[0] + 1, node_text(node), hops))
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
        prog="find_train_wrecks.py",
        description="Print one JSON object per train-wreck chain: path, line, expression, hops.",
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
        return find_wrecks(file.read_text(), str(file))
    return find_wrecks_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


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
