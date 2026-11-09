"""Hidden behavior check for `slack-channel`: slack works, old channels and the unknown-channel error still do."""
import unittest

from src.notifications import send

USER = {"email": "a@x.io", "phone": "555", "slack_id": "U1"}


class WhenSendingNotifications(unittest.TestCase):
    def test_slack_uses_the_slack_id(self) -> None:
        self.assertEqual(send("slack", USER, "hi"), "slack:U1:hi")

    def test_email_and_sms_are_unchanged(self) -> None:
        self.assertEqual((send("email", USER, "hi"), send("sms", USER, "hi")), ("email:a@x.io:hi", "sms:555:hi"))

    def test_unknown_channel_still_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            send("fax", USER, "hi")
