import unittest

from src.durations import to_seconds


class WhenConvertingDurations(unittest.TestCase):
    def test_minutes_are_sixty_seconds(self) -> None:
        self.assertEqual(to_seconds(2, "min"), 120)

    def test_hours_are_3600_seconds(self) -> None:
        self.assertEqual(to_seconds(1, "h"), 3600)
