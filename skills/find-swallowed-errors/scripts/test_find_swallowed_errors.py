import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from find_swallowed_errors import find_swallowed, main, source_files


def flagged(source: str) -> list[tuple[str, str, str]]:
    return [(f.name, f.handler, f.body) for f in find_swallowed(source, "m.py")]


class WhenHandlerBodyIsEmpty(unittest.TestCase):
    def test_pass_only_handler(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        pass"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "empty")])

    def test_ellipsis_only_handler(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except ValueError:\n        ..."
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "empty")])

    def test_docstring_only_handler(self) -> None:
        # arrange
        source = 'def f():\n    try:\n        a()\n    except Exception:\n        """todo"""'
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "empty")])

    def test_module_level_handler_reports_module(self) -> None:
        # arrange
        source = "try:\n    a()\nexcept Exception:\n    pass"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("<module>", "except", "empty")])


class WhenHandlerOnlyReturns(unittest.TestCase):
    def test_bare_return(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        return"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "return")])

    def test_return_fallback_value(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        return None"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "return")])

    def test_return_after_docstring_is_still_return_only(self) -> None:
        # arrange
        source = 'def f():\n    try:\n        a()\n    except Exception:\n        """swallow"""\n        return 0'
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "return")])


class WhenHandlerResponds(unittest.TestCase):
    def test_logging_call_is_not_flagged(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        log(e)"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [])

    def test_reraise_is_not_flagged(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        raise"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [])

    def test_log_then_return_is_not_flagged(self) -> None:
        # arrange — the log is an observable response to the error
        source = "def f():\n    try:\n        a()\n    except Exception as e:\n        log(e)\n        return None"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [])

    def test_assignment_is_not_flagged(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        seen = True"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [])


class WhenSeveralHandlersExist(unittest.TestCase):
    def test_only_swallowing_handlers_are_flagged(self) -> None:
        # arrange
        source = (
            "def f():\n    try:\n        a()\n"
            "    except ValueError:\n        pass\n"
            "    except KeyError:\n        raise\n"
            "    except Exception:\n        return None"
        )
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "empty"), ("f", "except", "return")])

    def test_try_star_swallow_is_flagged(self) -> None:
        # arrange
        source = "async def f():\n    try:\n        await a()\n    except* Exception:\n        pass"
        # act
        findings = flagged(source)
        # assert
        self.assertEqual(findings, [("f", "except", "empty")])


class WhenLocatingFindings(unittest.TestCase):
    def test_finding_records_line_and_path(self) -> None:
        # arrange
        source = "def f():\n    try:\n        a()\n    except Exception:\n        pass"
        # act
        findings = find_swallowed(source, "m.py")
        # assert
        self.assertEqual((findings[0].path, findings[0].line), ("m.py", 4))


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

    def test_unsupported_suffix_is_an_error(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp, "m.txt")
            target.write_text("x")
            # act / assert
            with self.assertRaises(FileNotFoundError):
                source_files(target)


class WhenRunningMain(unittest.TestCase):
    def test_finding_prints_json_and_exits_1(self) -> None:
        # arrange
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "m.py").write_text("try:\n    a()\nexcept Exception:\n    pass\n")
            # act
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([tmp])
        # assert
        self.assertEqual(code, 1)
        record = json.loads(out.getvalue())
        self.assertTrue(record["path"].endswith("m.py"))
        self.assertEqual(record["body"], "empty")

    def test_clean_file_exits_0(self) -> None:
        # arrange
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "m.py").write_text("def f():\n    return 1\n")
            # act
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([tmp])
        # assert
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")

    def test_missing_path_exits_2(self) -> None:
        # arrange
        err = io.StringIO()
        # act
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = main(["does-not-exist"])
        # assert
        self.assertEqual(code, 2)
        self.assertIn("does-not-exist", err.getvalue())

    def test_unparseable_file_warns_and_exits_2(self) -> None:
        # arrange
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "broken.py").write_text("def broken(:\n")
            # act
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = main([tmp])
        # assert
        self.assertEqual(code, 2)
        self.assertIn("broken.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
