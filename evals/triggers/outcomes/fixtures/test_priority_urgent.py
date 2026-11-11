"""Hidden behavior check for `priority-urgent`: urgent tickets get 2 hours, old priorities and the unknown-priority error still work."""
import unittest

from src.priorities import response_hours


class WhenSettingResponseDeadlines(unittest.TestCase):
    def test_urgent_tickets_get_two_hours(self) -> None:
        self.assertEqual(response_hours("urgent"), 2)

    def test_existing_priorities_are_unchanged(self) -> None:
        self.assertEqual((response_hours("low"), response_hours("normal"), response_hours("high")), (72, 24, 8))

    def test_unknown_priority_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            response_hours("critical")
