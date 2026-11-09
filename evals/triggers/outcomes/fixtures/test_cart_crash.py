"""Hidden behavior check for `cart-crash`: an empty cart must check out at zero; real carts are unchanged."""
import unittest

from src.checkout import checkout


class WhenCheckingOutAnEmptyCart(unittest.TestCase):
    def test_cart_without_items_key_totals_zero(self) -> None:
        self.assertEqual(checkout({}), {"total_cents": 0, "lines": 0})

    def test_cart_with_empty_items_totals_zero(self) -> None:
        self.assertEqual(checkout({"items": []}, "SAVE10"), {"total_cents": 0, "lines": 0})

    def test_real_cart_is_unchanged(self) -> None:
        cart = {"items": [{"price_cents": 500, "qty": 2}]}
        self.assertEqual(checkout(cart, "SAVE10"), {"total_cents": 900, "lines": 1})
