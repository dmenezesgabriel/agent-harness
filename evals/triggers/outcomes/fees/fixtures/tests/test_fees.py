import unittest

from src.fees import fee_cents


class WhenChargingProcessingFees(unittest.TestCase):
    def test_card_is_thirty_cents_plus_two_point_nine_percent(self) -> None:
        self.assertEqual(fee_cents("card", 10000), 320)

    def test_bank_transfer_is_flat(self) -> None:
        self.assertEqual(fee_cents("bank_transfer", 10000), 25)
