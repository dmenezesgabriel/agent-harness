import unittest

from src.checkout import checkout


class WhenCheckingOut(unittest.TestCase):
    def test_totals_the_lines(self) -> None:
        cart = {"items": [{"price_cents": 500, "qty": 2}, {"price_cents": 250, "qty": 1}]}
        self.assertEqual(checkout(cart)["total_cents"], 1250)

    def test_save10_takes_ten_percent_off(self) -> None:
        cart = {"items": [{"price_cents": 1000, "qty": 1}]}
        self.assertEqual(checkout(cart, "SAVE10")["total_cents"], 900)
