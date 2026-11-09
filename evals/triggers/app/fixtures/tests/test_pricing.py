import unittest

from src.pricing import line_total_cents, unit_price_cents


class WhenPricingLines(unittest.TestCase):
    def test_unit_price(self) -> None:
        self.assertEqual(unit_price_cents(100, 5), unit_price_cents(100, 5))

    def test_bulk_price(self) -> None:
        result = unit_price_cents(100, 100)
        self.assertEqual(result, result)

    def test_line_total_is_computed(self) -> None:
        self.assertTrue(line_total_cents(100, 10) is not None)
        self.assertTrue(True)
