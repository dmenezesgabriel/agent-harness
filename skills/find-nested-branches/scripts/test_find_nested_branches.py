import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from find_nested_branches import find_nested, main


def flagged(source: str) -> list[str]:
    return [f.name for f in find_nested(source, "m.py")]


class FlagsElseAndElif(unittest.TestCase):
    def test_else_branch(self) -> None:
        self.assertEqual(flagged("def f(x):\n    if x:\n        a()\n    else:\n        b()"), ["f"])

    def test_elif_branch(self) -> None:
        self.assertEqual(flagged("def f(x):\n    if x:\n        a()\n    elif y:\n        b()"), ["f"])

    def test_else_elif_counts(self) -> None:
        src = "def f(x):\n    if x:\n        a()\n    elif y:\n        b()\n    else:\n        c()"
        findings = find_nested(src, "m.py")
        self.assertEqual((findings[0].elses, findings[0].elifs), (1, 1))


class FlagsDeepNesting(unittest.TestCase):
    def test_loop_with_inner_if(self) -> None:
        self.assertEqual(flagged("def f(xs):\n    for x in xs:\n        if x:\n            a()"), ["f"])

    def test_if_in_if(self) -> None:
        self.assertEqual(flagged("def f(x):\n    if x:\n        if x > 1:\n            a()"), ["f"])


class IgnoresFlatCode(unittest.TestCase):
    def test_guard_cascade(self) -> None:
        self.assertEqual(flagged("def f(x):\n    if not x:\n        return\n    if x < 0:\n        return\n    a()"), [])

    def test_single_level_loop(self) -> None:
        self.assertEqual(flagged("def f(xs):\n    for x in xs:\n        a(x)"), [])

    def test_try_with_is_not_a_decision(self) -> None:
        src = "def f(p):\n    for line in open(p):\n        with lock:\n            use(line)"
        self.assertEqual(flagged(src), [])


class Main(unittest.TestCase):
    def test_bad_path_exit_2(self) -> None:
        self.assertEqual(main(["nonexistent-xyz"]), 2)

    def test_clean_file_exit_0(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
            handle.write("def f(x):\n    return x")
        self.assertEqual(main([handle.name]), 0)



    def test_broken_python_file_skipped_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.py").write_text("def f(x):\n    if x:\n        a()\n    else:\n        b()")
            Path(tmp, "broken.py").write_text("def broken(:\n")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main([tmp]), 1)
            self.assertIn("warning:", stderr.getvalue())

    def test_all_broken_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "broken.py").write_text("def broken(:\n")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([tmp]), 2)

    def test_unsupported_suffix_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "sample.rb")
            path.write_text("x = 1")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(path)]), 2)

if __name__ == "__main__":
    unittest.main()
