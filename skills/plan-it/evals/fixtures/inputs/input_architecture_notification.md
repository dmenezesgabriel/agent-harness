Plan this work as implementation task files. Create the files under `tasks/issues/` and `docs/adrs/`; do not return a prose-only plan and do not write root-level Markdown files.

We are adding the email delivery boundary for project member invitations to an existing SaaS app. A project owner will eventually enter an email address, and invitation delivery must go through a provider-agnostic boundary before endpoint work starts.

Constraints:
- The app already has users, projects, project owners, and authenticated API routes.
- Email delivery provider is intentionally not chosen yet. This should not block planning; create an ADR stub for the provider-agnostic delivery boundary and keep provider selection deferred.
- This eval only covers the provider-agnostic email boundary and a fake implementation for tests.
- Do not plan invitation send or accept endpoints in this eval.
- The plan should keep the system functional after every task.

Create the issue files and any ADR stubs needed.

If a decision remains unresolved, mark the dependent task HITL with the specific decision point instead of asking a clarification question.
