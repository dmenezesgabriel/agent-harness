from __future__ import annotations

from app.invites import DuplicateInviteError, InviteService


class InviteFlowModel:
    def __init__(self, service: InviteService | None = None) -> None:
        self.service = service or InviteService()
        self.form_email = ""
        self.error = None
        self.pending_invites = []
        self.submit_disabled = False

    def load(self) -> None:
        self.pending_invites = self.service.list_pending_invites()

    def submit(self, email: str) -> bool:
        self.submit_disabled = True
        self.error = None
        self.form_email = email
        try:
            self.service.create_invite(email)
        except DuplicateInviteError as exc:
            self.error = str(exc)
            self.submit_disabled = False
            return False
        self.pending_invites = self.service.list_pending_invites()
        self.form_email = ""
        self.submit_disabled = False
        return True
