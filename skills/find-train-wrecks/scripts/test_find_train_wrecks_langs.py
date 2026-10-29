import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from find_train_wrecks import find_wrecks_tree, main

try:
    import tree_sitter_language_pack  # noqa: F401
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


def chains(source: bytes, grammar: str) -> list[tuple[str, int]]:
    return [(f.expression, f.hops) for f in find_wrecks_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class TypeScript(unittest.TestCase):
    def test_attribute_chain(self) -> None:
        self.assertEqual(chains(b"const x = a.b.c.d;", "typescript"), [("a.b.c.d", 3)])

    def test_call_links_do_not_add_hops(self) -> None:
        self.assertEqual(chains(b"const y = a.b().c().d();", "typescript"), [("a.b().c().d()", 3)])

    def test_subscript_chain(self) -> None:
        self.assertEqual(chains(b"const z = a[b][c][d];", "typescript"), [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        self.assertEqual(chains(b"const w = this.a.b.c;", "typescript"), [])

    def test_reports_maximal_chain_once(self) -> None:
        self.assertEqual(chains(b"const x = a.b.c.d.e;", "typescript"), [("a.b.c.d.e", 4)])

    def test_two_hops_ignored(self) -> None:
        self.assertEqual(chains(b"const x = a.b.c;", "typescript"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class JavaScript(unittest.TestCase):
    def test_js_chain_uses_tsx_grammar(self) -> None:
        self.assertEqual(chains(b"const x = a.b.c.d;", "tsx"), [("a.b.c.d", 3)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Java(unittest.TestCase):
    def test_field_chain(self) -> None:
        self.assertEqual(chains(b"class A { Object f(){ return a.b.c.d; } }", "java"), [("a.b.c.d", 3)])

    def test_method_chain(self) -> None:
        self.assertEqual(chains(b"class A { Object f(){ return a.b().c().d(); } }", "java"),
                         [("a.b().c().d()", 3)])

    def test_array_chain(self) -> None:
        self.assertEqual(chains(b"class A { Object f(){ return a[b][c][d]; } }", "java"), [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        self.assertEqual(chains(b"class A { Object f(){ return this.a.b.c; } }", "java"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Kotlin(unittest.TestCase):
    def test_navigation_chain(self) -> None:
        self.assertEqual(chains(b"fun f() = a.b.c.d", "kotlin"), [("a.b.c.d", 3)])

    def test_call_chain(self) -> None:
        self.assertEqual(chains(b"fun f() { a.b().c().d() }", "kotlin"), [("a.b().c().d()", 3)])

    def test_optional_chain(self) -> None:
        self.assertEqual(chains(b"fun f() = a?.b?.c?.d", "kotlin"), [("a?.b?.c?.d", 3)])

    def test_index_chain(self) -> None:
        self.assertEqual(chains(b"fun f() = a[b][c][d]", "kotlin"), [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        self.assertEqual(chains(b"fun f() = this.a.b.c", "kotlin"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class Main(unittest.TestCase):
    def test_mixed_directory_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.ts").write_text("const x = a.b.c.d;")
            Path(tmp, "b.py").write_text("x = a.b.c.d")
            self.assertEqual(main([tmp]), 1)

    def test_syntax_error_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp, "bad.ts")
            bad.write_text("const x = ;;; class {")
            self.assertEqual(main([str(bad)]), 2)

    def test_broken_file_skipped_in_directory_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.ts").write_text("const x = a.b.c.d;")
            Path(tmp, "broken.ts").write_text("const x = ;;; class {")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main([tmp]), 1)
            self.assertIn("warning:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
