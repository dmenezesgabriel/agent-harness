import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from find_train_wrecks import find_wrecks, main, source_files


def chains(source: str) -> list[str]:
    return [f.expression for f in find_wrecks(source, "m.py")]


class WhenChainHasThreeOrMoreHops(unittest.TestCase):
    def test_three_attribute_hops(self) -> None:
        # arrange
        source = "x = a.b.c.d"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, ["a.b.c.d"])

    def test_call_links_count_toward_hops(self) -> None:
        # arrange
        source = "x = a.get_b().get_c().name"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, ["a.get_b().get_c().name"])

    def test_subscript_chain(self) -> None:
        # arrange
        source = 'x = cfg["db"]["pool"]["size"]'

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, ["cfg['db']['pool']['size']"])

    def test_reports_maximal_chain_once(self) -> None:
        # arrange
        source = "x = a.b.c.d.e"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, ["a.b.c.d.e"])

    def test_chain_in_call_argument(self) -> None:
        # arrange
        source = "f(a.b.c.d)"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, ["a.b.c.d"])


class WhenChainStaysUnderThreeHops(unittest.TestCase):
    def test_two_hops(self) -> None:
        # arrange
        source = "x = a.b.c"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, [])

    def test_self_first_hop_is_free(self) -> None:
        # arrange
        source = "def f(self):\n    return self.a.b.c"

        # act
        findings = chains(source)

        # assert
        self.assertEqual(findings, [])


class WhenInputIsInvalid(unittest.TestCase):
    def test_missing_path_returns_exit_code_2(self) -> None:
        # act
        exit_code = main(["nonexistent-xyz"])

        # assert
        self.assertEqual(exit_code, 2)

    def test_unsupported_suffix_returns_exit_code_2(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "sample.rb")
            path.write_text("x = 1")

            # act
            with contextlib.redirect_stderr(io.StringIO()):
                exit_code = main([str(path)])

        # assert
        self.assertEqual(exit_code, 2)


class WhenSourceCannotBeParsed(unittest.TestCase):
    def test_broken_file_is_skipped_with_warning(self) -> None:
        # arrange
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.py").write_text("x = a.b.c.d")
            Path(tmp, "broken.py").write_text("def broken(:\n")

            # act
            with contextlib.redirect_stderr(stderr):
                exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 1)
        self.assertIn("warning:", stderr.getvalue())

    def test_all_files_broken_returns_exit_code_2(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "broken.py").write_text("def broken(:\n")

            # act
            with contextlib.redirect_stderr(io.StringIO()):
                exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 2)


class WhenScanningDirectories(unittest.TestCase):
    def test_generated_dirs_are_skipped(self) -> None:
        # arrange
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "src").mkdir()
            Path(tmp, "src", "good.py").write_text("x = a.b.c.d")
            Path(tmp, "node_modules").mkdir()
            Path(tmp, "node_modules", "dep.py").write_text("x = a.b.c.d")

            # act
            with contextlib.redirect_stdout(stdout):
                exit_code = main([tmp])

        # assert
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)

    def test_generated_dir_is_scanned_when_named_explicitly(self) -> None:
        # arrange
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "build").mkdir()
            Path(tmp, "build", "good.py").write_text("x = a.b.c.d")

            # act
            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(Path(tmp, "build"))])

        # assert
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()

class WhenParsingCliArguments(unittest.TestCase):
    def test_help_exits_zero_and_documents_paths(self) -> None:
        # arrange
        out = io.StringIO()
        # act
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(out):
            main(["--help"])
        # assert
        self.assertEqual(raised.exception.code, 0)
        help_text = out.getvalue()
        self.assertIn("find_train_wrecks.py", help_text)
        self.assertIn("PATH [PATH ...]", help_text)
        self.assertIn("source file, or directory", help_text)
        self.assertIn("Print one JSON object", help_text)
        self.assertIn("Exit codes", help_text)
        self.assertNotIn("XX", help_text)

    def test_missing_path_arg_exits_two_with_usage_on_stderr(self) -> None:
        # arrange
        err = io.StringIO()
        # act
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(err):
            main([])
        # assert
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("usage", err.getvalue())

    def test_unsupported_suffix_reports_expected_extensions_on_stderr(self) -> None:
        # arrange
        err = io.StringIO()
        # act
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp, "x.txt")
            bad.write_text("x")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = main([str(bad)])
        # assert
        self.assertEqual(code, 2)
        self.assertIn(".txt", err.getvalue())
        self.assertIn("x.txt", err.getvalue())

    def test_missing_path_reports_not_a_file_or_directory_on_stderr(self) -> None:
        # arrange
        err, out = io.StringIO(), io.StringIO()
        # act
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["does-not-exist-xyz"])
        # assert
        self.assertEqual(code, 2)
        self.assertIn("not a file or directory", err.getvalue())
        self.assertNotIn("not a file or directory", out.getvalue())

    def test_empty_directory_exits_zero(self) -> None:
        # arrange / act
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = main([tmp])
        # assert
        self.assertEqual(code, 0)


class WhenDiscoveringSourceFiles(unittest.TestCase):
    def test_each_supported_suffix_is_accepted_as_file_arg(self) -> None:
        # arrange / act / assert — one subTest per suffix kills every set-membership mutant
        for suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".kts"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp, f"m{suffix}")
                target.write_text("")
                self.assertEqual(source_files(target), [target])

    def test_each_generated_directory_is_excluded(self) -> None:
        # arrange / act / assert — parameterize over _SKIP_DIRS + dotted dirs
        for skip in ("node_modules", "dist", "build", "target", "out", "vendor", "coverage", "__pycache__", ".hidden"):
            with self.subTest(skip=skip), tempfile.TemporaryDirectory() as tmp:
                sub = Path(tmp, skip)
                sub.mkdir()
                Path(sub, "m.py").write_text("x = 1")
                self.assertEqual(source_files(Path(tmp)), [])

class WhenWalkingDirectoryTrees(unittest.TestCase):
    def test_directory_scan_returns_supported_files_sorted(self) -> None:
        # arrange
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("b.py", "a.py", "sub/c.py", "x.txt"):
                target = Path(root, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x = 1")
            # act
            found = source_files(root)
        # assert
        self.assertEqual(found, [Path(root, "a.py"), Path(root, "b.py"), Path(root, "sub", "c.py")])

    def test_unparseable_file_reports_filename_on_stderr(self) -> None:
        # arrange
        err = io.StringIO()
        # act
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "broken.py").write_text("def broken(:\n")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = main([tmp])
        # assert
        self.assertEqual(code, 2)
        self.assertIn("broken.py", err.getvalue())
        self.assertNotIn("XX", err.getvalue())

class WhenCountingParsedFiles(unittest.TestCase):
    def test_broken_file_after_valid_one_does_not_reset_parsed_count(self) -> None:
        # arrange — sorted() puts a_ok.py before z_broken.py; `parsed =` reset would exit 2
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a_ok.py").write_text("def f(self):\n    return self.a.b.c.d")
            Path(tmp, "z_broken.py").write_text("def broken(:\n")
            out, err = io.StringIO(), io.StringIO()
            # act
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main([tmp])
        # assert
        self.assertNotEqual(code, 2)


class WhenReportingFindingPaths(unittest.TestCase):
    def test_finding_records_the_source_path(self) -> None:
        # arrange
        source = "def f(self):\n    return self.a.b.c.d"
        # act
        findings = find_wrecks(source, "m.py")
        # assert
        self.assertTrue(findings)
        self.assertEqual(findings[0].path, "m.py")

class WhenPrintingFindings(unittest.TestCase):
    def test_main_prints_each_finding_as_json_with_path(self) -> None:
        # arrange
        out = io.StringIO()
        # act
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp, "m.py")
            target.write_text("def f(self):\n    return self.a.b.c.d")
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([str(target)])
        # assert
        self.assertEqual(code, 1)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0]["path"].endswith("m.py"))
        self.assertIn('"expression": "self.a.b.c.d"'.replace("'", '"'), out.getvalue())

class WhenScanningTreeSitterFiles(unittest.TestCase):
    def test_main_reports_finding_path_for_ts_file(self) -> None:
        # arrange
        out = io.StringIO()
        # act
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp, "m.ts")
            target.write_text('const y = a.b.c.d;')
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main([str(target)])
        # assert
        self.assertEqual(code, 1)
        record = json.loads(out.getvalue())
        self.assertTrue(record["path"].endswith("m.ts"))
        self.assertIn('"expression": "a.b.c.d"', out.getvalue())
