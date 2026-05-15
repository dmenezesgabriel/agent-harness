from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Invite:
    email: str
    status: str = "pending"


@dataclass
class InviteRepository:
    invites: List[Invite] = field(default_factory=list)

    def add(self, invite: Invite) -> Invite:
        self.invites.append(invite)
        return invite

    def find_by_email(self, email: str) -> List[Invite]:
        normalized = email.strip().lower()
        return [invite for invite in self.invites if invite.email == normalized]


class DuplicateInviteError(Exception):
    pass


class InviteService:
    def __init__(self, repository: InviteRepository | None = None) -> None:
        self.repository = repository or InviteRepository()

    def create_invite(self, email: str) -> dict:
        normalized = email.strip().lower()
        existing = self.repository.find_by_email(normalized)
        if any(invite.status == "pending" for invite in existing):
            raise DuplicateInviteError(f"Invite already exists for {normalized}")
        invite = self.repository.add(Invite(email=normalized, status="pending"))
        return {"email": invite.email, "status": invite.status}

    def list_pending_invites(self) -> list[dict]:
        return [
            {"email": invite.email, "status": invite.status}
            for invite in self.repository.invites
            if invite.status == "pending"
        ]
