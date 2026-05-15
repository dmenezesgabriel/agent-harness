import unittest

from app.invites import DuplicateInviteError, Invite, InviteRepository, InviteService


class InviteServicePublicTests(unittest.TestCase):
    def test_duplicate_pending_invite_is_rejected(self):
        repo = InviteRepository(invites=[Invite(email="ada@example.com", status="pending")])
        service = InviteService(repo)
        with self.assertRaises(DuplicateInviteError):
            service.create_invite("ada@example.com")

    def test_new_invite_is_added(self):
        service = InviteService()
        created = service.create_invite("grace@example.com")
        self.assertEqual(created["email"], "grace@example.com")
        self.assertEqual(len(service.list_pending_invites()), 1)

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
        self.assertEqual(len(service.list_pending_invites()), 1)


if __name__ == "__main__":
    unittest.main()
