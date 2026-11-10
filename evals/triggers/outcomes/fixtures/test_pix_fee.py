"""Hidden behavior check for `pix-fee`: pix is 1% rounded down, old methods and the unknown-method error still work."""
import unittest

from src.fees import fee_cents


class WhenChargingProcessingFees(unittest.TestCase):
    def test_pix_is_one_percent_rounded_down(self) -> None:
        self.assertEqual((fee_cents("pix", 10000), fee_cents("pix", 199)), (100, 1))

    def test_existing_methods_are_unchanged(self) -> None:
        fees = (fee_cents("card", 10000), fee_cents("paypal", 10000), fee_cents("bank_transfer", 10000))
        self.assertEqual(fees, (320, 398, 25))

    def test_unknown_method_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            fee_cents("cash", 100)
