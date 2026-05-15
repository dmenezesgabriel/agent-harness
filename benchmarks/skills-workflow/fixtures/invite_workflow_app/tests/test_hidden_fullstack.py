import unittest

from app.invite_flow import InviteFlowModel
from app.invites import Invite, InviteRepository, InviteService


class InviteFlowHiddenTests(unittest.TestCase):
    def test_duplicate_error_reenables_submit_for_retry(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="pending")])
        model = InviteFlowModel(InviteService(repo))
        self.assertFalse(model.submit("ada@example.com"))
        self.assertFalse(model.submit_disabled)
        self.assertIn("ada@example.com", model.error)

    def test_load_shows_existing_pending_invites(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="pending")])
        model = InviteFlowModel(InviteService(repo))
        model.load()
        self.assertEqual(model.pending_invites, [{"email": "ada@example.com", "status": "pending"}])


if __name__ == "__main__":
    unittest.main()
