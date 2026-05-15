import unittest

from app.invites import Invite, InviteRepository, InviteService


class InviteServiceHiddenTests(unittest.TestCase):
    def test_archived_invite_does_not_block_new_pending_invite(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="archived")])
        service = InviteService(repo)
        created = service.create_invite("ada@example.com")
        self.assertEqual(created["status"], "pending")
        self.assertEqual(len(repo.invites), 2)

    def test_expired_invite_does_not_block_new_pending_invite(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="expired")])
        service = InviteService(repo)
        created = service.create_invite("ada@example.com")
        self.assertEqual(created["status"], "pending")


if __name__ == "__main__":
    unittest.main()
