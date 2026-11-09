import contextlib
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from importlib.util import find_spec
from pathlib import Path

from find_swallowed_errors import MissingTreeSitter, find_swallowed_tree, main, node_text

HAS_TREE_SITTER = find_spec("tree_sitter_language_pack") is not None


def swallowed(source: bytes, grammar: str) -> list[tuple[str, str, str]]:
    return [(f.name, f.handler, f.body) for f in find_swallowed_tree(source, f"m.{grammar}", grammar)]


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingTypeScript(unittest.TestCase):
    def test_empty_catch_is_flagged(self) -> None:
        # arrange
        source = b"function f(){ try { a() } catch (e) {} }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [("f", "catch", "empty")])

    def test_comment_only_catch_is_flagged(self) -> None:
        # arrange — a comment is not an observable response
        source = b"function f(){ try { a() } catch (e) { /* todo */ } }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [("f", "catch", "empty")])

    def test_return_only_catch_is_flagged(self) -> None:
        # arrange
        source = b"function f(){ try { a() } catch (e) { return null } }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [("f", "catch", "return")])

    def test_catch_that_logs_is_not_flagged(self) -> None:
        # arrange
        source = b"function f(){ try { a() } catch (e) { console.error(e) } }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [])

    def test_catch_that_logs_then_returns_is_not_flagged(self) -> None:
        # arrange — logging is an observable response even before the return
        source = b"function f(){ try { a() } catch (e) { console.error(e); return null } }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [])

    def test_promise_catch_empty_block_is_flagged(self) -> None:
        # arrange
        source = b"function f(){ p.catch(() => {}) }"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [("f", ".catch()", "empty")])

    def test_promise_catch_value_body_is_flagged(self) -> None:
        # arrange — returning null/undefined/fallback discards the rejection into a value
        for source in (b"p.catch(() => null)", b"p.catch(() => undefined)", b"p.catch(() => fallback)"):
            # act / assert
            self.assertEqual(swallowed(source, "typescript"), [("<module>", ".catch()", "return")])

    def test_promise_catch_return_statement_is_flagged(self) -> None:
        # arrange
        source = b"p.catch(e => { return })"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [("<module>", ".catch()", "return")])

    def test_promise_catch_with_invocation_is_not_flagged(self) -> None:
        # arrange — calling a handler is a response
        for source in (b"p.catch(e => handle(e))", b"p.catch(e => { console.error(e) })"):
            # act / assert
            self.assertEqual(swallowed(source, "typescript"), [])

    def test_other_members_named_differently_are_ignored(self) -> None:
        # arrange
        source = b"p.then(() => {}); p.catching(() => {})"
        # act / assert
        self.assertEqual(swallowed(source, "typescript"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingJava(unittest.TestCase):
    def test_empty_catch_is_flagged(self) -> None:
        # arrange
        source = b"class A { void f(){ try { a(); } catch (Exception e) {} } }"
        # act / assert
        self.assertEqual(swallowed(source, "java"), [("f", "catch", "empty")])

    def test_return_only_catch_is_flagged(self) -> None:
        # arrange
        source = b"class A { int f(){ try { a(); } catch (Exception e) { return 0; } } }"
        # act / assert
        self.assertEqual(swallowed(source, "java"), [("f", "catch", "return")])

    def test_catch_that_handles_is_not_flagged(self) -> None:
        # arrange
        source = b"class A { void f(){ try { a(); } catch (Exception e) { log(e); } } }"
        # act / assert
        self.assertEqual(swallowed(source, "java"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenParsingKotlin(unittest.TestCase):
    def test_empty_catch_is_flagged(self) -> None:
        # arrange
        source = b"fun f(){ try { a() } catch (e: Exception) { } }"
        # act / assert
        self.assertEqual(swallowed(source, "kotlin"), [("f", "catch", "empty")])

    def test_return_only_catch_is_flagged(self) -> None:
        # arrange
        source = b"fun f(){ try { a() } catch (e: Exception) { return } }"
        # act / assert
        self.assertEqual(swallowed(source, "kotlin"), [("f", "catch", "return")])

    def test_throw_in_catch_is_not_flagged(self) -> None:
        # arrange — a jump_expression that is not `return` must not pass as return-only
        source = b"fun f(){ try { a() } catch (e: Exception) { throw e } }"
        # act / assert
        self.assertEqual(swallowed(source, "kotlin"), [])

    def test_catch_that_handles_is_not_flagged(self) -> None:
        # arrange
        source = b"fun f(){ try { a() } catch (e: Exception) { log(e) } }"
        # act / assert
        self.assertEqual(swallowed(source, "kotlin"), [])


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenLocatingFindings(unittest.TestCase):
    def test_finding_line_is_one_based_position(self) -> None:
        # arrange
        source = b"const x = 1\nfunction f(){ try { a() } catch (e) {} }"
        # act
        findings = find_swallowed_tree(source, "m.ts", "typescript")
        # assert
        self.assertEqual(findings[0].line, 2)


class WhenTreeSitterIsMissing(unittest.TestCase):
    def test_import_error_raises_missing_tree_sitter(self) -> None:
        # arrange
        with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), self.assertRaises(MissingTreeSitter):
            find_swallowed_tree(b"x", "m.ts", "typescript")

    def test_main_returns_exit_code_2(self) -> None:
        # arrange
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "m.ts").write_text("function f(){}")
            # act
            with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": None}), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = main([tmp])
        # assert
        self.assertEqual(code, 2)
        self.assertIn("tree-sitter", err.getvalue())


@unittest.skipUnless(HAS_TREE_SITTER, "tree-sitter-language-pack not installed; run tests via uv")
class WhenSourceFailsToParse(unittest.TestCase):
    def test_parse_error_raises_syntax_error(self) -> None:
        # act / assert
        with self.assertRaises(SyntaxError):
            find_swallowed_tree(b"function {", "m.ts", "typescript")


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
        node.text = b"catch"
        # act / assert
        self.assertEqual(node_text(node), "catch")


if __name__ == "__main__":
    unittest.main()
