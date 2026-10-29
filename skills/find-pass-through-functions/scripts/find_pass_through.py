#!/usr/bin/env python3
# /// script
# dependencies = ["tree-sitter-language-pack"]
# ///
"""Report pass-through functions: bodies that only forward their own parameters to another call.

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

ArgShape = tuple[str, ...]
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_RECEIVERS = ("self", "cls")
_LANGUAGES = {
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".tsx": "tsx", ".js": "tsx", ".jsx": "tsx", ".mjs": "tsx", ".cjs": "tsx",
    ".java": "java",
    ".kt": "kotlin", ".kts": "kotlin",
}
_FAMILY = {"typescript": "ts", "tsx": "ts", "java": "java", "kotlin": "kotlin"}
_FUNCTIONS = {
    "ts": {"function_declaration", "function_expression", "generator_function_declaration",
           "generator_function", "method_definition", "arrow_function"},
    "java": {"method_declaration", "constructor_declaration"},
    "kotlin": {"function_declaration"},
}
_UNKNOWN = "?"


class MissingTreeSitter(RuntimeError):
    """tree-sitter-language-pack is not importable in this interpreter."""


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
    """Pass-through functions in Python `source`.

    >>> find_pass_throughs("def get(id):\\n    return repo.get(id)", "m.py")[0].callee
    'repo.get'
    """
    functions = [n for n in ast.walk(ast.parse(source, filename=path)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return [Finding(path, fn.lineno, fn.name, callee) for fn in functions if (callee := _pass_through_callee(fn))]


def _ts_params(fn: Any) -> list[str]:
    params = fn.child_by_field_name("parameters")
    if params is None:
        return []
    names = []
    for child in params.named_children:
        pattern = child.child_by_field_name("pattern") if child.type in {"required_parameter", "optional_parameter"} else None
        names.append(pattern.text.decode() if pattern is not None else _UNKNOWN)
    return names


def _ts_call(fn: Any) -> Any:
    body = fn.child_by_field_name("body")
    if body is None:
        return None
    if body.type == "call_expression":
        return body
    if body.type != "statement_block":
        return None
    statements = [c for c in body.named_children if c.type != "comment"]
    if len(statements) != 1 or statements[0].type not in {"return_statement", "expression_statement"}:
        return None
    inner = statements[0].named_children
    return inner[0] if len(inner) == 1 and inner[0].type == "call_expression" else None


def _ts_args(call: Any) -> list[str]:
    args = call.child_by_field_name("arguments")
    if args is None:
        return []
    return [c.text.decode() if c.type == "identifier" else _UNKNOWN for c in args.named_children]


def _ts_callee(call: Any) -> str | None:
    func = call.child_by_field_name("function")
    if func is None:
        return None
    if func.type == "member_expression":
        obj = func.child_by_field_name("object")
        if obj is not None and obj.type == "super":
            return None
    return func.text.decode()


def _java_params(fn: Any) -> list[str]:
    params = fn.child_by_field_name("parameters")
    if params is None:
        return []
    names = []
    for child in params.named_children:
        name = child.child_by_field_name("name") if child.type == "formal_parameter" else None
        names.append(name.text.decode() if name is not None else _UNKNOWN)
    return names


def _java_call(fn: Any) -> Any:
    body = fn.child_by_field_name("body")
    if body is None:
        return None
    statements = [c for c in body.named_children if c.type not in {"line_comment", "block_comment"}]
    if len(statements) != 1 or statements[0].type not in {"return_statement", "expression_statement"}:
        return None
    inner = statements[0].named_children
    return inner[0] if len(inner) == 1 and inner[0].type == "method_invocation" else None


def _java_args(call: Any) -> list[str]:
    args = call.child_by_field_name("arguments")
    if args is None:
        return []
    return [c.text.decode() if c.type == "identifier" else _UNKNOWN for c in args.named_children]


def _java_callee(call: Any) -> str | None:
    obj = call.child_by_field_name("object")
    if obj is not None and obj.type == "super":
        return None
    name = call.child_by_field_name("name")
    if name is None:
        return None
    return f"{obj.text.decode()}.{name.text.decode()}" if obj is not None else name.text.decode()


def _kotlin_params(fn: Any) -> list[str]:
    params = next((c for c in fn.children if c.type == "function_value_parameters"), None)
    if params is None:
        return []
    names = []
    for child in params.named_children:
        ident = next((c for c in child.named_children if c.type == "simple_identifier"), None) if child.type == "parameter" else None
        names.append(ident.text.decode() if ident is not None else _UNKNOWN)
    return names


def _kotlin_call(fn: Any) -> Any:
    body = next((c for c in fn.children if c.type == "function_body"), None)
    if body is None:
        return None
    if body.text.decode().lstrip().startswith("="):
        named = body.named_children
        return named[0] if len(named) == 1 and named[0].type == "call_expression" else None
    named = body.named_children
    if len(named) != 1 or named[0].type != "statements":
        return None
    statements = named[0].named_children
    if len(statements) != 1 or statements[0].type != "jump_expression":
        return None
    calls = [c for c in statements[0].named_children if c.type == "call_expression"]
    return calls[0] if len(calls) == 1 else None


def _kotlin_args(call: Any) -> list[str]:
    suffix = next((c for c in call.children if c.type == "call_suffix"), None)
    arguments = next((c for c in suffix.named_children if c.type == "value_arguments"), None) if suffix is not None else None
    if arguments is None:
        return []
    names = []
    for value in arguments.named_children:
        inner = value.named_children
        names.append(inner[0].text.decode() if len(inner) == 1 and inner[0].type == "simple_identifier" else _UNKNOWN)
    return names


def _kotlin_callee(call: Any) -> str | None:
    callee = call.children[0] if call.children else None
    if callee is None:
        return None
    text = callee.text.decode()
    return None if text.startswith(("super.", "super<")) else text


_SINGLE_CALL = {"ts": _ts_call, "java": _java_call, "kotlin": _kotlin_call}
_PARAMS = {"ts": _ts_params, "java": _java_params, "kotlin": _kotlin_params}
_ARGS = {"ts": _ts_args, "java": _java_args, "kotlin": _kotlin_args}
_CALLEE = {"ts": _ts_callee, "java": _java_callee, "kotlin": _kotlin_callee}


def _is_annotated(fn: Any, family: str) -> bool:
    if family == "ts":
        sibling = fn.prev_named_sibling
        return sibling is not None and sibling.type == "decorator"
    modifiers = next((c for c in fn.children if c.type == "modifiers"), None)
    if modifiers is None:
        return False
    return any(c.type in {"annotation", "marker_annotation"} for c in modifiers.named_children)


def _tree_pass_through_callee(fn: Any, family: str) -> str | None:
    if _is_annotated(fn, family):
        return None
    call = _SINGLE_CALL[family](fn)
    if call is None:
        return None
    params = _PARAMS[family](fn)
    args = _ARGS[family](call)
    if not params or _UNKNOWN in params or _UNKNOWN in args or params != args:
        return None
    return _CALLEE[family](call)


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


def find_pass_throughs_tree(source: bytes, path: str, grammar: str) -> list[Finding]:
    """Pass-through functions in TypeScript/JavaScript/Java/Kotlin `source`.

    >>> find_pass_throughs_tree(b"function f(x){ return repo.get(x) }", "m.ts", "typescript")[0].callee
    'repo.get'
    """
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError as error:
        raise MissingTreeSitter(
            "tree-sitter-language-pack is not installed; run via `uv run scripts/find_pass_through.py` "
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
        callee = _tree_pass_through_callee(fn, family)
        if callee is not None:
            findings.append(Finding(path, fn.start_point[0] + 1, _function_name(fn, family), callee))
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
                  and not any(part.startswith(".") for part in p.relative_to(target).parts))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="find_pass_through.py",
        description="Print one JSON object per pass-through function: path, line, name, callee.",
        epilog="Exit codes: 0 none found, 1 found, 2 bad input (missing path, unsupported file, no file parsed, bad flags).",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH",
                        help="source file, or directory searched recursively (.py, .ts, .tsx, .js, .jsx, .java, .kt, .kts)")
    return parser.parse_args(argv)


def _find_in_file(file: Path) -> list[Finding]:
    if file.suffix == ".py":
        return find_pass_throughs(file.read_text(), str(file))
    return find_pass_throughs_tree(file.read_bytes(), str(file), _LANGUAGES[file.suffix])


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
