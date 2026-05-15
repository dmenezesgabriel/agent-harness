import unittest

from app.invite_flow import InviteFlowModel
from app.invites import Invite, InviteRepository, InviteService


class InviteFlowPublicTests(unittest.TestCase):
    def test_submit_adds_pending_invite_and_clears_form(self):
        model = InviteFlowModel()
        self.assertTrue(model.submit("ada@example.com"))
        self.assertEqual(model.form_email, "")
        self.assertEqual(model.pending_invites, [{"email": "ada@example.com", "status": "pending"}])

    def test_duplicate_error_reenables_submit_for_retry(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="pending")])
        model = InviteFlowModel(InviteService(repo))

        self.assertFalse(model.submit("ada@example.com"))
        self.assertFalse(model.submit_disabled)
        self.assertIn("ada@example.com", model.error)


if __name__ == "__main__":
    unittest.main()
