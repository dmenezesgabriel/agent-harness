"""Hidden behavior check for `ingest-errors`: good rows load, and a bad line is surfaced, not silently dropped."""
import unittest

from src.ingest import load_rows


class WhenLoadingRows(unittest.TestCase):
    def test_good_lines_still_load(self) -> None:
        self.assertEqual(load_rows(["A,5", "B,7"]), [{"sku": "A", "price_cents": 5}, {"sku": "B", "price_cents": 7}])

    def test_a_bad_line_raises_or_logs_a_warning(self) -> None:
        try:
            with self.assertLogs(level="WARNING"):
                load_rows(["A,5", "B,not-a-price"])
        except AssertionError:
            self.fail("bad line was dropped silently: nothing raised and nothing logged")
        except Exception:  # noqa: BLE001 -- raising is an accepted way to surface it
            pass
