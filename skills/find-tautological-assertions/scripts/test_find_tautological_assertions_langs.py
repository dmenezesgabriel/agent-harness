import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_tautological_assertions import MissingTreeSitter, find_tautologies_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def tautologies(source: bytes, grammar: str) -> list[tuple[str, str]]:
    return [(f.name, f.kind) for f in find_tautologies_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_expect_same_operand_is_flagged(self) -> None:
        # arrange
        source = b"it('t', () => { expect(x).toBe(x) })"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [("<anonymous>", "same-operands")])

    def test_expect_different_operands_is_not_flagged(self) -> None:
        # arrange
        source = b"expect(x).toBe(y)"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [])

    def test_expect_true_truthy_is_flagged(self) -> None:
        # arrange
        source = b"expect(true).toBeTruthy()"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [("<module>", "always-true")])

    def test_assert_namespace_equal_is_flagged(self) -> None:
        # arrange
        for source in (b"assert.equal(x, x)", b"assert.strictEqual(x, x)", b"assert.deepEqual(x, x)"):
            # act / assert
            self.assertEqual(tautologies(source, "typescript"), [("<module>", "same-operands")])

    def test_assert_ok_true_is_flagged(self) -> None:
        # arrange
        source = b"assert.ok(true)"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [("<module>", "always-true")])

    def test_bare_assert_same_binary_is_flagged(self) -> None:
        # arrange
        source = b"assert(x === x)"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [("<module>", "same-operands")])

    def test_assert_namespace_different_operands_is_not_flagged(self) -> None:
        # arrange
        source = b"assert.strictEqual(x, y); assert.ok(ok)"
        # act / assert
        self.assertEqual(tautologies(source, "typescript"), [])

    def test_enclosing_function_name_is_reported(self) -> None:
        # arrange
        source = b"function t(){ expect(x).toBe(x) }"
        # act
        findings = find_tautologies_tree(source, "m.ts", "typescript")
        # assert
        self.assertEqual(findings[0].name, "t")


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_assert_equals_same_operand_is_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assertEquals(x, x); } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [("t", "same-operands")])

    def test_assert_true_literal_is_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assertTrue(true); } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [("t", "always-true")])

    def test_assert_true_same_binary_is_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assertTrue(a == a); } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [("t", "same-operands")])

    def test_assert_false_literal_is_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assertFalse(false); } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [("t", "always-true")])

    def test_assert_statement_same_binary_is_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assert x == x; } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [("t", "same-operands")])

    def test_real_assertions_are_not_flagged(self) -> None:
        # arrange
        source = b"class A { void t(){ assertEquals(x, y); assertTrue(ok); assert z == w; } }"
        # act / assert
        self.assertEqual(tautologies(source, "java"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_assert_equals_same_operand_is_flagged(self) -> None:
        # arrange
        source = b"fun t(){ assertEquals(x, x) }"
        # act / assert
        self.assertEqual(tautologies(source, "kotlin"), [("t", "same-operands")])

    def test_assert_true_literal_is_flagged(self) -> None:
        # arrange
        source = b"fun t(){ assertTrue(true) }"
        # act / assert
        self.assertEqual(tautologies(source, "kotlin"), [("t", "always-true")])

    def test_bare_assert_same_equality_is_flagged(self) -> None:
        # arrange
        source = b"fun t(){ assert(x == x) }"
        # act / assert
        self.assertEqual(tautologies(source, "kotlin"), [("t", "same-operands")])

    def test_real_assertions_are_not_flagged(self) -> None:
        # arrange
        source = b"fun t(){ assertEquals(x, y) assertTrue(ok) assert(x == y) }"
        # act / assert
        self.assertEqual(tautologies(source, "kotlin"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenLocatingFindings(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const a = 1\nexpect(x).toBe(x)"
        # act
        findings = find_tautologies_tree(source, "m.ts", "typescript")
        # assert
        self.assertEqual(findings[0].line, 2)


class WhenTreeSitterIsMissing(unittest.TestCase):
    def test_import_error_raises_missing_tree_sitter(self) -> None:
        # arrange
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), self.assertRaises(MissingTreeSitter):
            find_tautologies_tree(b"x", "m.ts", "typescript")

    def test_main_returns_exit_code_2(self) -> None:
        # arrange
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "m.ts").write_text("const x = 1")
            # act
            with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = main([tmp])
        # assert
        self.assertEqual(code, 2)


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenSourceFailsToParse(unittest.TestCase):
    def test_parse_error_raises_syntax_error(self) -> None:
        # act / assert
        with self.assertRaises(SyntaxError):
            find_tautologies_tree(b"function {", "m.ts", "typescript")


class WhenDecodingNodeText(unittest.TestCase):
    def test_node_without_text_decodes_to_empty(self) -> None:
        # arrange
        node = mock.Mock()
        node.text = None
        # act / assert
        self.assertEqual(node_text(node), "")


if __name__ == "__main__":
    unittest.main()
