import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_train_wrecks import MissingTreeSitter, find_wrecks, find_wrecks_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def chains(source: bytes, grammar: str) -> list[tuple[str, int]]:
    return [(f.expression, f.hops) for f in find_wrecks_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_attribute_chain(self) -> None:
        # arrange
        source = b"const x = a.b.c.d;"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [("a.b.c.d", 3)])

    def test_call_links_do_not_add_hops(self) -> None:
        # arrange
        source = b"const y = a.b().c().d();"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [("a.b().c().d()", 3)])

    def test_subscript_chain(self) -> None:
        # arrange
        source = b"const z = a[b][c][d];"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        # arrange
        source = b"const w = this.a.b.c;"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_reports_maximal_chain_once(self) -> None:
        # arrange
        source = b"const x = a.b.c.d.e;"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [("a.b.c.d.e", 4)])

    def test_two_hops_ignored(self) -> None:
        # arrange
        source = b"const x = a.b.c;"

        # act
        findings = chains(source, "typescript")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJavaScript(unittest.TestCase):
    def test_js_chain_uses_tsx_grammar(self) -> None:
        # arrange
        source = b"const x = a.b.c.d;"

        # act
        findings = chains(source, "tsx")

        # assert
        self.assertEqual(findings, [("a.b.c.d", 3)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_field_chain(self) -> None:
        # arrange
        source = b"class A { Object f(){ return a.b.c.d; } }"

        # act
        findings = chains(source, "java")

        # assert
        self.assertEqual(findings, [("a.b.c.d", 3)])

    def test_method_chain(self) -> None:
        # arrange
        source = b"class A { Object f(){ return a.b().c().d(); } }"

        # act
        findings = chains(source, "java")

        # assert
        self.assertEqual(findings, [("a.b().c().d()", 3)])

    def test_array_chain(self) -> None:
        # arrange
        source = b"class A { Object f(){ return a[b][c][d]; } }"

        # act
        findings = chains(source, "java")

        # assert
        self.assertEqual(findings, [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        # arrange
        source = b"class A { Object f(){ return this.a.b.c; } }"

        # act
        findings = chains(source, "java")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_navigation_chain(self) -> None:
        # arrange
        source = b"fun f() = a.b.c.d"

        # act
        findings = chains(source, "kotlin")

        # assert
        self.assertEqual(findings, [("a.b.c.d", 3)])

    def test_call_chain(self) -> None:
        # arrange
        source = b"fun f() { a.b().c().d() }"

        # act
        findings = chains(source, "kotlin")

        # assert
        self.assertEqual(findings, [("a.b().c().d()", 3)])

    def test_optional_chain(self) -> None:
        # arrange
        source = b"fun f() = a?.b?.c?.d"

        # act
        findings = chains(source, "kotlin")

        # assert
        self.assertEqual(findings, [("a?.b?.c?.d", 3)])

    def test_index_chain(self) -> None:
        # arrange
        source = b"fun f() = a[b][c][d]"

        # act
        findings = chains(source, "kotlin")

        # assert
        self.assertEqual(findings, [("a[b][c][d]", 3)])

    def test_this_first_hop_is_free(self) -> None:
        # arrange
        source = b"fun f() = this.a.b.c"

        # act
        findings = chains(source, "kotlin")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenScanningMixedDirectories(unittest.TestCase):
    def test_mixed_python_and_ts_directory_finds_both(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.ts").write_text("const x = a.b.c.d;")
            Path(tmp, "b.py").write_text("x = a.b.c.d")

            # act
            exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 1)

    def test_single_broken_ts_file_returns_exit_code_2(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp, "bad.ts")
            bad.write_text("const x = ;;; class {")

            # act
            exit_code = main([str(bad)])

        # assert
        self.assertEqual(exit_code, 2)

    def test_broken_ts_file_is_skipped_with_warning(self) -> None:
        # arrange
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.ts").write_text("const x = a.b.c.d;")
            Path(tmp, "broken.ts").write_text("const x = ;;; class {")

            # act
            with contextlib.redirect_stderr(stderr):
                exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 1)
        self.assertIn("warning:", stderr.getvalue())


class WhenTreeSitterPackageIsMissing(unittest.TestCase):
    def test_find_wrecks_tree_raises_missing_tree_sitter(self) -> None:
        # arrange
        source = b"const x = 1;"

        # act / assert
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                self.assertRaisesRegex(MissingTreeSitter, "tree-sitter-language-pack") as raised:
            find_wrecks_tree(source, "m.ts", "typescript")
        self.assertIn("PEP 723", str(raised.exception))
        self.assertNotIn("XX", str(raised.exception))

    def test_main_returns_exit_code_2(self) -> None:
        # arrange
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.ts").write_text("const x = 1;")

            # act
            with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                    contextlib.redirect_stderr(stderr):
                exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 2)
        self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

class WhenDecodingNodeText(unittest.TestCase):
    def test_node_without_text_decodes_to_empty(self) -> None:
        # arrange
        node = mock.Mock()
        node.text = None
        # act / assert
        self.assertEqual(node_text(node), "")

    def test_node_text_decodes_bytes(self) -> None:
        # arrange
        node = mock.Mock()
        node.text = b"const"
        # act / assert
        self.assertEqual(node_text(node), "const")
class WhenReportingLineNumbers(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const z = 1;\nconst y = a.b.c.d;"
        # act
        findings = find_wrecks_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].line, findings[0].expression), (2, "a.b.c.d"))

class WhenNamingKotlinFunctions(unittest.TestCase):
    def test_kotlin_function_reports_its_name(self) -> None:
        # arrange
        source = b"val y = a.b.c.d"
        # act
        findings = find_wrecks_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].expression, "a.b.c.d")

class WhenNamingDeclaredFunctions(unittest.TestCase):
    def test_named_declaration_reports_its_name(self) -> None:
        # arrange
        source = b"function f() { return a.b.c.d; }"
        # act
        findings = find_wrecks_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].expression, findings[0].hops), ("a.b.c.d", 3))

class WhenHandlingLanguageSpecificConstructs(unittest.TestCase):
    def test_call_result_chain_stops_at_call(self) -> None:
        # arrange
        source = "def f(self):\n    return make().a.b.c"
        # act
        findings = find_wrecks(source, "m.py")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].hops, 3)

    def test_java_member_chain_counts_hops(self) -> None:
        # arrange
        source = b"class S { int f() { return a.b.c.d; } }"
        # act
        findings = find_wrecks_tree(source, "m.java", "java")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].expression, findings[0].hops), ("a.b.c.d", 3))
