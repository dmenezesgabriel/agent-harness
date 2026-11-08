import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_feature_envy import MissingTreeSitter, find_envy_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def envy(source: bytes, grammar: str) -> list[tuple[str, str, list[str]]]:
    return [(f.name, f.target, f.attrs) for f in find_envy_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_three_attribute_reads(self) -> None:
        # arrange
        source = b"function f(u){ return u.a + u.b + u.c }"

        # act
        findings = envy(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        # arrange
        source = b"function f(u){ return u.a + u.b }"

        # act
        findings = envy(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_method_reads_count(self) -> None:
        # arrange
        source = b"function f(u){ return u.getA() + u.getB() + u.getC() }"

        # act
        findings = envy(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", "u", ["getA", "getB", "getC"])])

    def test_nested_chain_reads_only_first_link(self) -> None:
        # arrange
        source = b"function f(u){ return u.a.b + u.a.c + u.a.d }"

        # act
        findings = envy(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_this_is_not_a_parameter(self) -> None:
        # arrange
        source = b"class A { m(){ return this.a + this.b + this.c } }"

        # act
        findings = envy(source, "typescript")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJavaScript(unittest.TestCase):
    def test_reads_via_tsx_grammar(self) -> None:
        # arrange
        source = b"function f(u){ return u.a + u.b + u.c }"

        # act
        findings = envy(source, "tsx")

        # assert
        self.assertEqual(findings, [("f", "u", ["a", "b", "c"])])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_three_field_reads(self) -> None:
        # arrange
        source = b"class A { int f(U u){ return u.a + u.b + u.c; } }"

        # act
        findings = envy(source, "java")

        # assert
        self.assertEqual(findings, [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        # arrange
        source = b"class A { int f(U u){ return u.a + u.b; } }"

        # act
        findings = envy(source, "java")

        # assert
        self.assertEqual(findings, [])

    def test_method_reads_count(self) -> None:
        # arrange
        source = b"class A { int f(U u){ return u.getA() + u.getB() + u.getC(); } }"

        # act
        findings = envy(source, "java")

        # assert
        self.assertEqual(findings, [("f", "u", ["getA", "getB", "getC"])])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_three_property_reads(self) -> None:
        # arrange
        source = b"fun f(u: U) = u.a + u.b + u.c"

        # act
        findings = envy(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", "u", ["a", "b", "c"])])

    def test_two_reads_ignored(self) -> None:
        # arrange
        source = b"fun f(u: U) = u.a + u.b"

        # act
        findings = envy(source, "kotlin")

        # assert
        self.assertEqual(findings, [])

    def test_method_reads_count(self) -> None:
        # arrange
        source = b"fun f(u: U) = u.getA() + u.getB() + u.getC()"

        # act
        findings = envy(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", "u", ["getA", "getB", "getC"])])

    def test_this_is_not_a_parameter(self) -> None:
        # arrange
        source = b"fun f() = this.a + this.b + this.c"

        # act
        findings = envy(source, "kotlin")

        # assert
        self.assertEqual(findings, [])


class WhenTreeSitterPackageIsMissing(unittest.TestCase):
    def test_find_envy_tree_raises_missing_tree_sitter(self) -> None:
        # arrange
        source = b"function f(){}"

        # act / assert
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                self.assertRaisesRegex(MissingTreeSitter, "tree-sitter-language-pack") as raised:
            find_envy_tree(source, "m.ts", "typescript")
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


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenSourceFailsToParse(unittest.TestCase):
    def test_parse_error_raises_syntax_error(self) -> None:
        # arrange
        source = b"f((( }{"

        # act / assert
        with self.assertRaises(SyntaxError):
            find_envy_tree(source, "m.ts", "typescript")


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
class WhenNamingAnonymousFunctions(unittest.TestCase):
    def test_declarator_arrow_reports_variable_name(self) -> None:
        # arrange
        # arrange — declarator parent names it, object-pair parent names it, bare call arg stays anonymous
        findings = find_envy_tree(b"const f = (u) => u.a + u.b + u.c;", "m.ts", "typescript")
        # act / assert
        self.assertEqual((findings[0].name, findings[0].target), ("f", "u"))

    def test_pair_arrow_reports_pair_key_as_name(self) -> None:
        # arrange
        source = b"const o = { m: (u) => u.a + u.b + u.c };"
        # act
        findings = find_envy_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "m")

    def test_call_arg_arrow_reports_anonymous_name(self) -> None:
        # arrange
        source = b"use((u) => u.a + u.b + u.c);"
        # act
        findings = find_envy_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "<anonymous>")


class WhenReportingLineNumbers(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const z = 1;\nconst f = (u) => u.a + u.b + u.c;"
        # act
        findings = find_envy_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].line, 2)

class WhenNamingKotlinFunctions(unittest.TestCase):
    def test_kotlin_function_reports_its_name(self) -> None:
        # arrange
        source = b"fun f(u: U) = u.a + u.b + u.c"
        # act
        findings = find_envy_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")

class WhenNamingDeclaredFunctions(unittest.TestCase):
    def test_named_declaration_reports_its_name(self) -> None:
        # arrange
        source = b"function f(u) { return u.a + u.b + u.c; }"
        # act
        findings = find_envy_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")

class WhenHandlingLanguageSpecificConstructs(unittest.TestCase):
    def test_java_method_reads_foreign_fields(self) -> None:
        # arrange
        source = b"class S { int f(U u) { return u.a + u.b + u.c; } }"
        # act
        findings = find_envy_tree(source, "m.java", "java")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].name, findings[0].target), ("f", "u"))

    def test_ts_optional_parameter_is_counted(self) -> None:
        # arrange
        source = b"function f(u, v = 1) { return u.a + u.b + u.c; }"
        # act
        findings = find_envy_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].target, "u")

    def test_kotlin_block_body_counts_hits(self) -> None:
        # arrange
        source = b"fun f(u: U) { return u.a + u.b + u.c }"
        # act
        findings = find_envy_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")
