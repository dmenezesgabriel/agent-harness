import unittest

from find_nested_branches import find_nested_tree, main

try:
    import tree_sitter_language_pack  # noqa: F401
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


def nested(source: bytes, grammar: str) -> list[tuple[str, int, int, int]]:
    return [(f.name, f.elses, f.elifs, f.depth) for f in find_nested_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class TypeScript(unittest.TestCase):
    def test_else(self) -> None:
        self.assertEqual(nested(b"function f(x){ if (x) { a() } else { b() } }", "typescript"),
                         [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        # depth 2 matches the Python detector: elif is a nested If in orelse.
        self.assertEqual(nested(b"function f(x){ if (x) { a() } else if (y) { b() } else { c() } }", "typescript"),
                         [("f", 1, 1, 2)])

    def test_nested_decision_depth(self) -> None:
        self.assertEqual(nested(b"function f(x){ if (x) { if (y) { a() } } }", "typescript"),
                         [("f", 0, 0, 2)])

    def test_arrow_function_named_from_declarator(self) -> None:
        self.assertEqual(nested(b"const g = (x) => { if (x) { a() } else { b() } };", "typescript"),
                         [("g", 1, 0, 1)])

    def test_switch_counts_as_decision(self) -> None:
        self.assertEqual(nested(b"function f(x){ if (x) { switch (y) { case 1: break; } } }", "typescript"),
                         [("f", 0, 0, 2)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class JavaScript(unittest.TestCase):
    def test_else_via_tsx_grammar(self) -> None:
        self.assertEqual(nested(b"function f(x){ if (x) { a() } else { b() } }", "tsx"), [("f", 1, 0, 1)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Java(unittest.TestCase):
    def test_else(self) -> None:
        self.assertEqual(nested(b"class A { int f(int x){ if (x>0) { return 1; } else { return 0; } } }", "java"),
                         [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        self.assertEqual(nested(b"class A { int f(int x){ if (x>0) { return 1; } else if (x<0) { return -1; } else { return 0; } } }", "java"),
                         [("f", 1, 1, 2)])

    def test_nested_decision_depth(self) -> None:
        self.assertEqual(nested(b"class A { void f(int x){ if (x>0) { for (;;) { } } } }", "java"),
                         [("f", 0, 0, 2)])

    def test_switch_counts_as_decision(self) -> None:
        self.assertEqual(nested(b"class A { void f(int x){ if (x>0) { switch (x) { case 1: break; } } } }", "java"),
                         [("f", 0, 0, 2)])

    def test_flat_function_ignored(self) -> None:
        self.assertEqual(nested(b"class A { void f(int x){ g(x); } }", "java"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Kotlin(unittest.TestCase):
    def test_statement_else(self) -> None:
        self.assertEqual(nested(b"fun f(x: Int) { if (x > 0) { a() } else { b() } }", "kotlin"),
                         [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        self.assertEqual(nested(b"fun f(x: Int) { if (x > 0) { a() } else if (x < 0) { b() } else { c() } }", "kotlin"),
                         [("f", 1, 1, 2)])

    def test_value_position_if_ignored(self) -> None:
        self.assertEqual(nested(b"fun g() = if (true) 1 else 2", "kotlin"), [])
        self.assertEqual(nested(b"fun f() { val y = if (true) 1 else 2 }", "kotlin"), [])

    def test_nested_decision_depth(self) -> None:
        self.assertEqual(nested(b"fun f(x: Int) { if (x > 0) { while (true) { a() } } }", "kotlin"),
                         [("f", 0, 0, 2)])

    def test_when_counts_as_decision(self) -> None:
        self.assertEqual(nested(b"fun f(x: Int) { if (x > 0) { when (x) { 1 -> a() } } }", "kotlin"),
                         [("f", 0, 0, 2)])

    def test_flat_function_ignored(self) -> None:
        self.assertEqual(nested(b"fun f(x: Int) { g(x) }", "kotlin"), [])


if __name__ == "__main__":
    unittest.main()
