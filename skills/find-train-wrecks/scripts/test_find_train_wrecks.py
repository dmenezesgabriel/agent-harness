import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from find_train_wrecks import find_wrecks, main


def chains(source: str) -> list[str]:
    return [f.expression for f in find_wrecks(source, "m.py")]


class FlagsLongChains(unittest.TestCase):
    def test_three_attribute_hops(self) -> None:
        self.assertEqual(chains("x = a.b.c.d"), ["a.b.c.d"])

    def test_call_links_count_toward_hops(self) -> None:
        self.assertEqual(chains("x = a.get_b().get_c().name"), ["a.get_b().get_c().name"])

    def test_subscript_chain(self) -> None:
        self.assertEqual(chains('x = cfg["db"]["pool"]["size"]'), ["cfg['db']['pool']['size']"])

    def test_reports_maximal_chain_once(self) -> None:
        self.assertEqual(chains("x = a.b.c.d.e"), ["a.b.c.d.e"])

    def test_chain_in_call_argument(self) -> None:
        self.assertEqual(chains("f(a.b.c.d)"), ["a.b.c.d"])


class IgnoresShortChains(unittest.TestCase):
    def test_two_hops(self) -> None:
        self.assertEqual(chains("x = a.b.c"), [])

    def test_self_first_hop_is_free(self) -> None:
        self.assertEqual(chains("def f(self):\n    return self.a.b.c"), [])


class Main(unittest.TestCase):
    def test_bad_path_exit_2(self) -> None:
        self.assertEqual(main(["nonexistent-xyz"]), 2)



    def test_broken_python_file_skipped_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.py").write_text("x = a.b.c.d")
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
