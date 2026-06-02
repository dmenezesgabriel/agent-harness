# Task: Integrate SendGrid Email Provider for Invitations

## Summary

Add email notification when a user is invited to a project. The SendGrid SDK (`sendgrid` package) exposes `send_email(to: str, subject: str, body: str)` on the client object. The SDK is a third-party library we do not control.

## Acceptance Criteria

- AC-1: When an invitation is recorded, an email is sent via SendGrid
- AC-2: The invitation service must not import SendGrid directly — it should depend on a project-owned abstraction
- AC-3: Tests use a fake email sender, not a real SendGrid client
- AC-4: All unit tests pass with `pytest tests/unit/`

## File Locations

- Implementation: `src/notifications/` and `src/invitations/`
- Tests: `tests/unit/`

## Non-Functional Requirements

- NFR-1: No provider SDK imports in domain or application logic
- NFR-2: Swapping to a different email provider should require no changes to the invitation service

## Out of Scope

- Multiple email providers simultaneously (only SendGrid initially)
- Email templates, attachments, or delivery status polling
