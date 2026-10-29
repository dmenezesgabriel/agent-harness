import unittest

from find_feature_envy import find_envy_tree, main

try:
    import tree_sitter_language_pack  # noqa: F401
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


def envy(source: bytes, grammar: str) -> list[tuple[str, str, list[str]]]:
    return [(f.name, f.target, f.attrs) for f in find_envy_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class TypeScript(unittest.TestCase):
    def test_three_attribute_reads(self) -> None:
        self.assertEqual(envy(b"function f(u){ return u.a + u.b + u.c }", "typescript"),
                         [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        self.assertEqual(envy(b"function f(u){ return u.a + u.b }", "typescript"), [])

    def test_method_reads_count(self) -> None:
        self.assertEqual(envy(b"function f(u){ return u.getA() + u.getB() + u.getC() }", "typescript"),
                         [("f", "u", ["getA", "getB", "getC"])])

    def test_nested_chain_reads_only_first_link(self) -> None:
        self.assertEqual(envy(b"function f(u){ return u.a.b + u.a.c + u.a.d }", "typescript"), [])

    def test_this_is_not_a_parameter(self) -> None:
        self.assertEqual(envy(b"class A { m(){ return this.a + this.b + this.c } }", "typescript"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class JavaScript(unittest.TestCase):
    def test_reads_via_tsx_grammar(self) -> None:
        self.assertEqual(envy(b"function f(u){ return u.a + u.b + u.c }", "tsx"), [("f", "u", ["a", "b", "c"])])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Java(unittest.TestCase):
    def test_three_field_reads(self) -> None:
        self.assertEqual(envy(b"class A { int f(U u){ return u.a + u.b + u.c; } }", "java"),
                         [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        self.assertEqual(envy(b"class A { int f(U u){ return u.a + u.b; } }", "java"), [])

    def test_method_reads_count(self) -> None:
        self.assertEqual(envy(b"class A { int f(U u){ return u.getA() + u.getB() + u.getC(); } }", "java"),
                         [("f", "u", ["getA", "getB", "getC"])])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Kotlin(unittest.TestCase):
    def test_three_property_reads(self) -> None:
        self.assertEqual(envy(b"fun f(u: U) = u.a + u.b + u.c", "kotlin"), [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        self.assertEqual(envy(b"fun f(u: U) = u.a + u.b", "kotlin"), [])

    def test_method_reads_count(self) -> None:
        self.assertEqual(envy(b"fun f(u: U) = u.getA() + u.getB() + u.getC()", "kotlin"),
                         [("f", "u", ["getA", "getB", "getC"])])

    def test_this_is_not_a_parameter(self) -> None:
        self.assertEqual(envy(b"fun f() = this.a + this.b + this.c", "kotlin"), [])


if __name__ == "__main__":
    unittest.main()
