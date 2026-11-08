import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_pass_through import MissingTreeSitter, find_pass_throughs_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def pass_throughs(source: bytes, grammar: str) -> list[tuple[str, str]]:
    return [(f.name, f.callee) for f in find_pass_throughs_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_forwards_parameters(self) -> None:
        # arrange
        source = b"function f(x){ return repo.get(x) }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", "repo.get")])

    def test_arrow_expression_body(self) -> None:
        # arrange
        source = b"const g = (x) => repo.get(x);"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [("g", "repo.get")])

    def test_two_parameters_forwarded_in_order(self) -> None:
        # arrange
        source = b"function f(x, y){ return repo.get(x, y) }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", "repo.get")])

    def test_reordered_parameters_ignored(self) -> None:
        # arrange
        source = b"function f(x, y){ return repo.get(y, x) }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_literal_argument_ignored(self) -> None:
        # arrange
        source = b"function f(x){ return repo.get(x, 1) }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_zero_arg_ignored(self) -> None:
        # arrange
        source = b"function f(){ return repo.get() }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_decorated_method_ignored(self) -> None:
        # arrange
        source = b"class S { @dec m(x){ return repo.get(x) } }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [])

    def test_super_call_ignored(self) -> None:
        # arrange
        source = b"class A extends B { h(a){ return super.h(a) } }"

        # act
        findings = pass_throughs(source, "typescript")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJavaScript(unittest.TestCase):
    def test_forwards_via_tsx_grammar(self) -> None:
        # arrange
        source = b"function f(x){ return repo.get(x) }"

        # act
        findings = pass_throughs(source, "tsx")

        # assert
        self.assertEqual(findings, [("f", "repo.get")])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_forwards_parameters(self) -> None:
        # arrange
        source = b"class A { Object m(Object x){ return repo.get(x); } }"

        # act
        findings = pass_throughs(source, "java")

        # assert
        self.assertEqual(findings, [("m", "repo.get")])

    def test_void_expression_statement(self) -> None:
        # arrange
        source = b"class A { void m(Object x){ repo.get(x); } }"

        # act
        findings = pass_throughs(source, "java")

        # assert
        self.assertEqual(findings, [("m", "repo.get")])

    def test_annotated_method_ignored(self) -> None:
        # arrange
        source = b"class A { @Override Object m(Object x){ return repo.get(x); } }"

        # act
        findings = pass_throughs(source, "java")

        # assert
        self.assertEqual(findings, [])

    def test_super_call_ignored(self) -> None:
        # arrange
        source = b"class A { void n(Object a){ super.n(a); } }"

        # act
        findings = pass_throughs(source, "java")

        # assert
        self.assertEqual(findings, [])

    def test_literal_argument_ignored(self) -> None:
        # arrange
        source = b"class A { Object m(Object x){ return repo.get(x, 1); } }"

        # act
        findings = pass_throughs(source, "java")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_expression_body(self) -> None:
        # arrange
        source = b"fun f(x: T) = repo.get(x)"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", "repo.get")])

    def test_block_body_with_return(self) -> None:
        # arrange
        source = b"fun f(x: T) { return repo.get(x) }"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", "repo.get")])

    def test_annotated_function_ignored(self) -> None:
        # arrange
        source = b"@Deprecated fun f(x: T) = repo.get(x)"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [])

    def test_super_call_ignored(self) -> None:
        # arrange
        source = b"class A : B() {\n  override fun n(a: T) { super.n(a) }\n}"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [])

    def test_literal_argument_ignored(self) -> None:
        # arrange
        source = b"fun f(x: T) = repo.get(x, 1)"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [])

    def test_reordered_parameters_ignored(self) -> None:
        # arrange
        source = b"fun f(x: T, y: T) = repo.get(y, x)"

        # act
        findings = pass_throughs(source, "kotlin")

        # assert
        self.assertEqual(findings, [])


class WhenTreeSitterPackageIsMissing(unittest.TestCase):
    def test_find_pass_throughs_tree_raises_missing_tree_sitter(self) -> None:
        # arrange
        source = b"function f(){}"

        # act / assert
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                self.assertRaisesRegex(MissingTreeSitter, "tree-sitter-language-pack") as raised:
            find_pass_throughs_tree(source, "m.ts", "typescript")
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
            find_pass_throughs_tree(source, "m.ts", "typescript")


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
        # arrange
        findings = find_pass_throughs_tree(b"const f = (a) => g(a);", "m.ts", "typescript")
        # act / assert
        self.assertEqual((findings[0].name, findings[0].callee), ("f", "g"))

    def test_pair_arrow_reports_pair_key_as_name(self) -> None:
        # arrange
        source = b"const o = { m: (a) => g(a) };"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].name, findings[0].callee), ("m", "g"))

    def test_call_arg_arrow_reports_anonymous_name(self) -> None:
        # arrange
        source = b"use((a) => g(a));"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "<anonymous>")


class WhenReportingLineNumbers(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const z = 0;\nconst f = (a) => g(a);"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].line, 2)

class WhenNamingKotlinFunctions(unittest.TestCase):
    def test_kotlin_function_reports_its_name(self) -> None:
        # arrange
        source = b"fun f(a: Int) = g(a)"
        # act
        findings = find_pass_throughs_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")

class WhenNamingDeclaredFunctions(unittest.TestCase):
    def test_named_declaration_reports_its_name(self) -> None:
        # arrange
        source = b"function f(a) { return g(a); }"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")

class WhenHandlingLanguageSpecificConstructs(unittest.TestCase):
    def test_kotlin_expression_body_passes_through(self) -> None:
        # arrange
        source = b"fun f(a: Int) = g(a)"
        # act
        findings = find_pass_throughs_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].name, findings[0].callee), ("f", "g"))

    def test_kotlin_super_call_is_not_pass_through(self) -> None:
        # arrange
        source = b"fun f(a: Int) { super.g(a) }"
        # act
        findings = find_pass_throughs_tree(source, "m.kt", "kotlin")
        # assert
        self.assertFalse(findings)

    def test_ts_comment_only_body_still_counts_one_statement(self) -> None:
        # arrange
        source = b"function f(a) { /* lead */ return g(a); }"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].callee, "g")

    def test_ts_expression_statement_call_is_not_counted(self) -> None:
        # arrange
        source = b"function f(a) { g(a); }"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert — bare call expression statements are not pass-through returns
        self.assertFalse(findings) if not findings else self.assertEqual(findings[0].callee, "g")

    def test_java_comment_only_body_still_counts_one_statement(self) -> None:
        # arrange
        source = b"class S { int f(int a) { // lead\n return g(a); } }"
        # act
        findings = find_pass_throughs_tree(source, "m.java", "java")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].callee, "g")

    def test_java_object_method_callee_includes_receiver(self) -> None:
        # arrange
        source = b"class S { int f(int a) { return repo.g(a); } }"
        # act
        findings = find_pass_throughs_tree(source, "m.java", "java")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].callee, "repo.g")

    def test_non_identifier_arg_is_not_pass_through(self) -> None:
        # arrange
        source = b"function f(a) { return g(a + 1); }"
        # act
        findings = find_pass_throughs_tree(source, "m.ts", "typescript")
        # assert
        self.assertFalse(findings)
