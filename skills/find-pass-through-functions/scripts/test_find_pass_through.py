import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from find_pass_through import find_pass_throughs, main


def callees(source: str) -> list[str]:
    return [f.callee for f in find_pass_throughs(source, "m.py")]


class FlagsForwarding(unittest.TestCase):
    def test_method_forwarding_same_args(self) -> None:
        self.assertEqual(callees("class S:\n    def get(self, id):\n        return self.repo.get(id)"), ["self.repo.get"])

    def test_async_await_forwarding(self) -> None:
        self.assertEqual(callees("async def get(id):\n    return await repo.get(id)"), ["repo.get"])

    def test_star_and_keyword_forwarding(self) -> None:
        self.assertEqual(callees("def f(a, *rest, k, **opts):\n    return g(a, *rest, k=k, **opts)"), ["g"])

    def test_docstring_is_ignored(self) -> None:
        self.assertEqual(callees('def f(a):\n    "doc"\n    return g(a)'), ["g"])


class IgnoresRealWork(unittest.TestCase):
    def test_transformed_argument(self) -> None:
        self.assertEqual(callees("def f(a):\n    return g(a + 1)"), [])

    def test_reordered_arguments(self) -> None:
        self.assertEqual(callees("def f(a, b):\n    return g(b, a)"), [])

    def test_extra_argument(self) -> None:
        self.assertEqual(callees("def f(a):\n    return g(a, 1)"), [])

    def test_decorated_function(self) -> None:
        self.assertEqual(callees("@cache\ndef f(a):\n    return g(a)"), [])

    def test_super_call(self) -> None:
        self.assertEqual(callees("class C:\n    def f(self, a):\n        return super().f(a)"), [])

    def test_zero_argument_function(self) -> None:
        self.assertEqual(callees("def now():\n    return clock.now()"), [])

    def test_more_than_one_statement(self) -> None:
        self.assertEqual(callees("def f(a):\n    log(a)\n    return g(a)"), [])


class CommandLine(unittest.TestCase):
    def run_main(self, source: str) -> int:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            Path(tmp, "m.py").write_text(source)
            return main([tmp])

    def run_main_on(self, target: Path) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main([str(target)])

    def test_exit_1_when_found(self) -> None:
        self.assertEqual(self.run_main("def f(a):\n    return g(a)"), 1)

    def test_exit_0_when_clean(self) -> None:
        self.assertEqual(self.run_main("def f(a):\n    return a"), 0)

    def test_exit_2_on_syntax_error(self) -> None:
        self.assertEqual(self.run_main("def f(:"), 2)

    def test_exit_2_on_missing_path(self) -> None:
        self.assertEqual(main(["/nonexistent/path"]), 2)

    def test_finds_inside_hidden_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp, ".hidden", "proj")
            target.mkdir(parents=True)
            (target / "m.py").write_text("def f(a):\n    return g(a)")
            self.assertEqual(self.run_main_on(target), 1)

    def test_skips_hidden_subdirectory_of_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".venv").mkdir()
            Path(tmp, ".venv", "x.py").write_text("def f(a):\n    return g(a)")
            self.assertEqual(self.run_main_on(Path(tmp)), 0)

    def test_prints_one_json_object_per_finding(self) -> None:
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(out):
            Path(tmp, "m.py").write_text("def f(a):\n    return g(a)")
            main([tmp])
        record = json.loads(out.getvalue())
        self.assertEqual((record["line"], record["name"], record["callee"]), (1, "f", "g"))

    def test_help_documents_exit_codes(self) -> None:
        out = io.StringIO()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(out):
            main(["--help"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("Exit codes", out.getvalue())

    def test_exit_2_without_paths(self) -> None:
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            main([])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
