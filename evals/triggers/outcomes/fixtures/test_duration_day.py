"""Hidden behavior check for `duration-day`: a day is 86400 seconds, old units and the unknown-unit error still work."""
import unittest

from src.durations import to_seconds


class WhenConvertingDurations(unittest.TestCase):
    def test_a_day_is_86400_seconds(self) -> None:
        self.assertEqual((to_seconds(1, "day"), to_seconds(3, "day")), (86400, 259200))

    def test_existing_units_are_unchanged(self) -> None:
        self.assertEqual((to_seconds(5, "s"), to_seconds(2, "min"), to_seconds(1, "h")), (5, 120, 3600))

    def test_unknown_unit_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            to_seconds(1, "week")
