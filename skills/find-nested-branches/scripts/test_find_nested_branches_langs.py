import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_nested_branches import MissingTreeSitter, find_nested_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def nested(source: bytes, grammar: str) -> list[tuple[str, int, int, int]]:
    return [(f.name, f.elses, f.elifs, f.depth) for f in find_nested_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_else(self) -> None:
        # arrange
        source = b"function f(x){ if (x) { a() } else { b() } }"

        # act
        findings = nested(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        # depth 2 matches the Python detector: elif is a nested If in orelse.
        # arrange
        source = b"function f(x){ if (x) { a() } else if (y) { b() } else { c() } }"

        # act
        findings = nested(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", 1, 1, 2)])

    def test_nested_decision_depth(self) -> None:
        # arrange
        source = b"function f(x){ if (x) { if (y) { a() } } }"

        # act
        findings = nested(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])

    def test_arrow_function_named_from_declarator(self) -> None:
        # arrange
        source = b"const g = (x) => { if (x) { a() } else { b() } };"

        # act
        findings = nested(source, "typescript")

        # assert
        self.assertEqual(findings, [("g", 1, 0, 1)])

    def test_switch_counts_as_decision(self) -> None:
        # arrange
        source = b"function f(x){ if (x) { switch (y) { case 1: break; } } }"

        # act
        findings = nested(source, "typescript")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJavaScript(unittest.TestCase):
    def test_else_via_tsx_grammar(self) -> None:
        # arrange
        source = b"function f(x){ if (x) { a() } else { b() } }"

        # act
        findings = nested(source, "tsx")

        # assert
        self.assertEqual(findings, [("f", 1, 0, 1)])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_else(self) -> None:
        # arrange
        source = b"class A { int f(int x){ if (x>0) { return 1; } else { return 0; } } }"

        # act
        findings = nested(source, "java")

        # assert
        self.assertEqual(findings, [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        # arrange
        source = b"class A { int f(int x){ if (x>0) { return 1; } else if (x<0) { return -1; } else { return 0; } } }"

        # act
        findings = nested(source, "java")

        # assert
        self.assertEqual(findings, [("f", 1, 1, 2)])

    def test_nested_decision_depth(self) -> None:
        # arrange
        source = b"class A { void f(int x){ if (x>0) { for (;;) { } } } }"

        # act
        findings = nested(source, "java")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])

    def test_switch_counts_as_decision(self) -> None:
        # arrange
        source = b"class A { void f(int x){ if (x>0) { switch (x) { case 1: break; } } } }"

        # act
        findings = nested(source, "java")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])

    def test_flat_function_ignored(self) -> None:
        # arrange
        source = b"class A { void f(int x){ g(x); } }"

        # act
        findings = nested(source, "java")

        # assert
        self.assertEqual(findings, [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_statement_else(self) -> None:
        # arrange
        source = b"fun f(x: Int) { if (x > 0) { a() } else { b() } }"

        # act
        findings = nested(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", 1, 0, 1)])

    def test_else_if_counts_elif(self) -> None:
        # arrange
        source = b"fun f(x: Int) { if (x > 0) { a() } else if (x < 0) { b() } else { c() } }"

        # act
        findings = nested(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", 1, 1, 2)])

    def test_value_position_if_ignored(self) -> None:
        # arrange
        expression_body = b"fun g() = if (true) 1 else 2"
        val_assignment = b"fun f() { val y = if (true) 1 else 2 }"

        # act
        expression_findings = nested(expression_body, "kotlin")
        val_findings = nested(val_assignment, "kotlin")

        # assert
        self.assertEqual(expression_findings, [])
        self.assertEqual(val_findings, [])

    def test_nested_decision_depth(self) -> None:
        # arrange
        source = b"fun f(x: Int) { if (x > 0) { while (true) { a() } } }"

        # act
        findings = nested(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])

    def test_when_counts_as_decision(self) -> None:
        # arrange
        source = b"fun f(x: Int) { if (x > 0) { when (x) { 1 -> a() } } }"

        # act
        findings = nested(source, "kotlin")

        # assert
        self.assertEqual(findings, [("f", 0, 0, 2)])

    def test_flat_function_ignored(self) -> None:
        # arrange
        source = b"fun f(x: Int) { g(x) }"

        # act
        findings = nested(source, "kotlin")

        # assert
        self.assertEqual(findings, [])


class WhenTreeSitterPackageIsMissing(unittest.TestCase):
    def test_find_nested_tree_raises_missing_tree_sitter(self) -> None:
        # arrange
        source = b"function f(){}"

        # act / assert
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                self.assertRaisesRegex(MissingTreeSitter, "tree-sitter-language-pack") as raised:
            find_nested_tree(source, "m.ts", "typescript")
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
            find_nested_tree(source, "m.ts", "typescript")


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
        findings = find_nested_tree(b"const f = (x) => { if (x) { a(); } else { b(); } };", "m.ts", "typescript")
        # act / assert
        self.assertEqual((findings[0].name, findings[0].elses), ("f", 1))

    def test_pair_arrow_reports_pair_key_as_name(self) -> None:
        # arrange
        source = b"const o = { m: (x) => { if (x) { a(); } else { b(); } } };"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].name, findings[0].elses), ("m", 1))

    def test_call_arg_arrow_reports_anonymous_name(self) -> None:
        # arrange
        source = b"use((x) => { if (x) { a(); } else { b(); } });"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "<anonymous>")


class WhenReportingLineNumbers(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const z = 1;\nfunction f(x) { if (x) { a(); } else { b(); } }"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].line, 2)

class WhenNamingKotlinFunctions(unittest.TestCase):
    def test_kotlin_function_reports_its_name(self) -> None:
        # arrange
        source = b"fun f(x: Int) { if (x > 0) { a() } else { b() } }"
        # act
        findings = find_nested_tree(source, "m.kt", "kotlin")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")


class WhenNamingDeclaredFunctions(unittest.TestCase):
    def test_named_declaration_reports_its_name(self) -> None:
        # arrange
        source = b"function f(x) { if (x) { a(); } else { b(); } }"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "f")

class WhenHandlingLanguageSpecificConstructs(unittest.TestCase):
    def test_ts_else_if_counts_as_elif(self) -> None:
        # arrange
        source = b"function f(x) { if (x) { a(); } else if (x > 1) { b(); } }"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].elses, findings[0].elifs), (0, 1))

    def test_ts_if_else_counts_else(self) -> None:
        # arrange
        source = b"function f(x) { if (x) { a(); } else { b(); } }"
        # act
        findings = find_nested_tree(source, "m.ts", "typescript")
        # assert
        self.assertTrue(findings)
        self.assertEqual((findings[0].elses, findings[0].depth), (1, 1))

    def test_kotlin_when_expression_counts_alternative(self) -> None:
        # arrange
        source = b"fun f(x: Int) { when (x) { 1 -> a(); else -> b() } }"
        # act
        findings = find_nested_tree(source, "m.kt", "kotlin")
        # assert — `when` alternatives are not counted as branches
        self.assertFalse(findings)
