import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from find_tautological_assertions import find_tautologies, main, source_files


def flagged(source: str) -> list[tuple[str, str]]:
    return [(f.name, f.kind) for f in find_tautologies(source, "t.py")]


class WhenAssertComparesIdenticalOperands(unittest.TestCase):
    def test_equality_with_itself(self) -> None:
        # arrange
        source = "def t():\n    assert x == x"
        # act / assert
        self.assertEqual(flagged(source), [("t", "same-operands")])

    def test_identity_with_itself(self) -> None:
        # arrange
        source = "def t():\n    assert x is x"
        # act / assert
        self.assertEqual(flagged(source), [("t", "same-operands")])

    def test_different_operands_are_not_flagged(self) -> None:
        # arrange
        source = "def t():\n    assert x == y"
        # act / assert
        self.assertEqual(flagged(source), [])

    def test_chain_with_mixed_operands_is_not_flagged(self) -> None:
        # arrange
        source = "def t():\n    assert x == x == y"
        # act / assert
        self.assertEqual(flagged(source), [])

    def test_inequality_with_itself_is_not_flagged(self) -> None:
        # arrange — `x != x` cannot pass; dead differently
        source = "def t():\n    assert x != x"
        # act / assert
        self.assertEqual(flagged(source), [])


class WhenAssertIsConstant(unittest.TestCase):
    def test_assert_true_literal(self) -> None:
        # arrange
        source = "def t():\n    assert True"
        # act / assert
        self.assertEqual(flagged(source), [("t", "always-true")])

    def test_assert_truthy_literal(self) -> None:
        # arrange
        source = "def t():\n    assert 1"
        # act / assert
        self.assertEqual(flagged(source), [("t", "always-true")])

    def test_assert_false_is_not_flagged(self) -> None:
        # arrange — `assert False` fails, it does not pass vacuously
        source = "def t():\n    assert False"
        # act / assert
        self.assertEqual(flagged(source), [])


class WhenUsingUnittestAsserts(unittest.TestCase):
    def test_assert_equal_identical_args(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertEqual(x, x)"
        # act / assert
        self.assertEqual(flagged(source), [("t", "same-operands")])

    def test_assert_equal_with_message_still_flags(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertEqual(x, x, 'must match')"
        # act / assert
        self.assertEqual(flagged(source), [("t", "same-operands")])

    def test_assert_equal_different_args(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertEqual(x, y)"
        # act / assert
        self.assertEqual(flagged(source), [])

    def test_assert_true_literal(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertTrue(True)"
        # act / assert
        self.assertEqual(flagged(source), [("t", "always-true")])

    def test_assert_false_literal(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertFalse(False)"
        # act / assert
        self.assertEqual(flagged(source), [("t", "always-true")])

    def test_assert_true_same_operands(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertTrue(a == a)"
        # act / assert
        self.assertEqual(flagged(source), [("t", "same-operands")])

    def test_assert_true_variable_is_not_flagged(self) -> None:
        # arrange
        source = "def t(self):\n    self.assertTrue(ok)"
        # act / assert
        self.assertEqual(flagged(source), [])

    def test_non_assert_calls_are_ignored(self) -> None:
        # arrange
        source = "def t():\n    check(x, x)\n    assert_that(x)"
        # act / assert
        self.assertEqual(flagged(source), [])


class WhenLocatingFindings(unittest.TestCase):
    def test_finding_records_line_path_and_assertion(self) -> None:
        # arrange
        source = "x = 1\ndef t():\n    assert x == x"
        # act
        findings = find_tautologies(source, "t.py")
        # assert
        self.assertEqual((findings[0].path, findings[0].line), ("t.py", 3))
        self.assertEqual(findings[0].assertion, "assert x == x")

    def test_module_level_assert_reports_module(self) -> None:
        # arrange
        source = "assert x == x"
        # act
        findings = find_tautologies(source, "t.py")
        # assert
        self.assertEqual(findings[0].name, "<module>")


class WhenListingSourceFiles(unittest.TestCase):
    def test_directory_is_walked_sorted_and_skips_noise(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("b.py", "a.py", "sub/c.py", "x.txt", "node_modules/d.py"):
                target = Path(root, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x = 1")
            # act
            found = source_files(root)
        # assert
        self.assertEqual(found, [Path(root, "a.py"), Path(root, "b.py"), Path(root, "sub", "c.py")])

    def test_missing_path_is_an_error(self) -> None:
        # act / assert
        with self.assertRaises(FileNotFoundError):
            source_files(Path("does-not-exist"))


class WhenRunningMain(unittest.TestCase):
    def test_finding_prints_json_and_exits_1(self) -> None:
        # arrange
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "t.py").write_text("assert x == x\n")
            # act
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([tmp])
        # assert
        self.assertEqual(code, 1)
        record = json.loads(out.getvalue())
        self.assertTrue(record["path"].endswith("t.py"))
        self.assertEqual(record["kind"], "same-operands")

    def test_clean_file_exits_0(self) -> None:
        # arrange
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "t.py").write_text("assert x == y\n")
            # act
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([tmp])
        # assert
        self.assertEqual(code, 0)

    def test_missing_path_exits_2(self) -> None:
        # arrange
        err = io.StringIO()
        # act
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = main(["does-not-exist"])
        # assert
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
