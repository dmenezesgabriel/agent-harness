# PRD Rules

Use these rules to produce product requirements documents that are concrete, bounded, and free of implementation assumptions.

## Minimum viable PRD

A PRD is ready to write when all four items are either stated in the brief or derivable from context:

1. **Problem statement** — what is broken, missing, or painful and for whom
2. **At least one persona** — a role with a specific pain point
3. **At least one user story** — a concrete goal a persona needs to achieve
4. **At least one measurable success metric** — a number or observable event, not a feeling

If any item is missing and cannot be derived, ask for it before writing. Ask one item at a time.

## Request type classification

Classify the request before writing:

- `new-product`: No prior codebase or domain model. The product does not exist yet.
- `new-feature`: Adding user-facing behavior to an existing product. Domain model exists.
- `behavior-change`: Modifying existing behavior. Existing users are affected; migration or communication may be required.

State the type in the PRD frontmatter under `request-type`. If unclear, ask with numbered alternatives, one marked `(recommended)`.

## Problem statement rules

- Write what is broken, missing, or painful — not how to fix it.
- Name who experiences the problem.
- Do not include solution language ("we will build", "the system should", "the feature will").
- Length: 2–4 sentences.

Good:
- "Team leads must open each project individually to see its current status. During stand-up they spend 10–15 minutes collecting status that should take under 2 minutes."

Bad:
- "We need a dashboard that shows all projects. The dashboard should have filters and sorting."

## Persona rules

- Name the persona by role or job-to-be-done, not by fictional demographics.
- State the specific pain point, not a generic description.
- Include only personas who directly experience the problem or will use the new behavior.
- Do not invent personas not implied by the brief.

Good:
- Team Lead — cannot see cross-project status without opening each project manually.
- Developer — receives notifications for projects they are not assigned to.

Bad:
- Power User — wants more features.
- Admin — manages the system.

## Success metric rules

Every metric must be measurable. Apply the SMART test: Specific, Measurable, Achievable, Relevant, Time-bound.

- State the baseline (current value or "unknown").
- State the target (a number, ratio, or observable event).
- State how it will be measured.

Good:
- Reduce time-to-first-action from 8 minutes (measured via session replay) to under 2 minutes.
- Increase week-1 retention from 42% to 55%, measured via cohort analysis.
- Zero unhandled errors on the dashboard route, measured via error monitoring.

Bad:
- Improve performance.
- Better onboarding.
- Users feel more productive.

At least one metric is required. If no metric can be defined, flag it as an open question — do not skip the section.

## Non-goal rules

At least one explicit non-goal is required in every PRD.

A non-goal names something a stakeholder might reasonably expect to be included but will not be. Without non-goals, scope creep starts from unspoken assumptions.

Good:
- Does not include mobile app support — web only for this release.
- Does not redesign the existing project settings page.
- Does not cover external collaborator access — only internal team members.

Bad:
- Out of scope.
- Not in this sprint.

## Constraint rules

State only constraints explicitly mentioned in the brief or clearly implied by the project context (compliance, existing integrations, team size, deadline).

Do not invent constraints speculatively.

Valid constraint types:
- Technical: "Must integrate with the existing PostgreSQL schema."
- Business: "Must not require a pricing plan change for existing users."
- Compliance: "Must not store PII outside the EU."
- Integration: "Must use the existing authentication middleware."

## Open question rules

List only questions that would block scope, design, or success metric definition if unanswered.

Good:
- Does export include archived projects or only active ones?
- Should notifications respect per-user timezone or project timezone?

Bad:
- What tech stack should we use? (Architecture question, not a PRD question.)
- How should we implement the database schema? (Implementation question.)

## Clarification protocol

Ask one question at a time. Each question must include numbered alternatives, one marked `(recommended)`, concrete and mutually exclusive.

Walk decisions in this order: who has the problem → what the problem is → what success looks like → what is out of scope.

Never ask for information already present in the brief or CONTEXT.md.
