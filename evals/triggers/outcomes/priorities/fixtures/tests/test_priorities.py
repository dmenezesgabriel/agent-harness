import unittest

from src.priorities import response_hours


class WhenSettingResponseDeadlines(unittest.TestCase):
    def test_normal_tickets_get_a_day(self) -> None:
        self.assertEqual(response_hours("normal"), 24)

    def test_high_tickets_get_eight_hours(self) -> None:
        self.assertEqual(response_hours("high"), 8)
