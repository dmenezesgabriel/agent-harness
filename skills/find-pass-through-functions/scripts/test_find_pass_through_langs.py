import unittest

from find_pass_through import find_pass_throughs_tree, main

try:
    import tree_sitter_language_pack  # noqa: F401
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


def pass_throughs(source: bytes, grammar: str) -> list[tuple[str, str]]:
    return [(f.name, f.callee) for f in find_pass_throughs_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class TypeScript(unittest.TestCase):
    def test_forwards_parameters(self) -> None:
        self.assertEqual(pass_throughs(b"function f(x){ return repo.get(x) }", "typescript"), [("f", "repo.get")])

    def test_arrow_expression_body(self) -> None:
        self.assertEqual(pass_throughs(b"const g = (x) => repo.get(x);", "typescript"), [("g", "repo.get")])

    def test_two_parameters_forwarded_in_order(self) -> None:
        self.assertEqual(pass_throughs(b"function f(x, y){ return repo.get(x, y) }", "typescript"), [("f", "repo.get")])

    def test_reordered_parameters_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"function f(x, y){ return repo.get(y, x) }", "typescript"), [])

    def test_literal_argument_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"function f(x){ return repo.get(x, 1) }", "typescript"), [])

    def test_zero_arg_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"function f(){ return repo.get() }", "typescript"), [])

    def test_decorated_method_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"class S { @dec m(x){ return repo.get(x) } }", "typescript"), [])

    def test_super_call_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"class A extends B { h(a){ return super.h(a) } }", "typescript"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class JavaScript(unittest.TestCase):
    def test_forwards_via_tsx_grammar(self) -> None:
        self.assertEqual(pass_throughs(b"function f(x){ return repo.get(x) }", "tsx"), [("f", "repo.get")])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Java(unittest.TestCase):
    def test_forwards_parameters(self) -> None:
        self.assertEqual(pass_throughs(b"class A { Object m(Object x){ return repo.get(x); } }", "java"),
                         [("m", "repo.get")])

    def test_void_expression_statement(self) -> None:
        self.assertEqual(pass_throughs(b"class A { void m(Object x){ repo.get(x); } }", "java"),
                         [("m", "repo.get")])

    def test_annotated_method_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"class A { @Override Object m(Object x){ return repo.get(x); } }", "java"), [])

    def test_super_call_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"class A { void n(Object a){ super.n(a); } }", "java"), [])

    def test_literal_argument_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"class A { Object m(Object x){ return repo.get(x, 1); } }", "java"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Kotlin(unittest.TestCase):
    def test_expression_body(self) -> None:
        self.assertEqual(pass_throughs(b"fun f(x: T) = repo.get(x)", "kotlin"), [("f", "repo.get")])

    def test_block_body_with_return(self) -> None:
        self.assertEqual(pass_throughs(b"fun f(x: T) { return repo.get(x) }", "kotlin"), [("f", "repo.get")])

    def test_annotated_function_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"@Deprecated fun f(x: T) = repo.get(x)", "kotlin"), [])

    def test_super_call_ignored(self) -> None:
        source = b"class A : B() {\n  override fun n(a: T) { super.n(a) }\n}"
        self.assertEqual(pass_throughs(source, "kotlin"), [])

    def test_literal_argument_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"fun f(x: T) = repo.get(x, 1)", "kotlin"), [])

    def test_reordered_parameters_ignored(self) -> None:
        self.assertEqual(pass_throughs(b"fun f(x: T, y: T) = repo.get(y, x)", "kotlin"), [])


if __name__ == "__main__":
    unittest.main()
