---
name: change-validation
description: Use this skill when you need to validate a completed change, run the smallest relevant checks, fix failing tests or regressions, confirm acceptance criteria or Definition of Done, and verify readiness before merge. Do not use for initial issue framing or broad exploratory audits of unrelated code.
---

## Purpose

Validate a defined code change after implementation is code-complete by confirming scope, acceptance criteria, Definition of Done, and relevant quality gates.

Run the smallest relevant final verification set, investigate failures, apply only narrow in-scope fixes that are required to complete validation, and report pass/fail status, residual risk, and merge readiness.

Use `skills/issue-definition` when acceptance criteria, Definition of Done, or scope are still unclear. Use `skills/implementation-workflow` when the main task is still implementing the change rather than validating it.

Use this skill for requests like:
- validate this change
- run checks and fix failures
- confirm acceptance criteria
- verify Definition of Done
- make sure this is ready to merge
- check for regressions after the fix

This skill is language-agnostic.

## When to Use / Not Use

Use this skill for targeted post-implementation verification and correction of a defined, already-implemented change.

Do not use it for:
- initial issue framing or solution design
- broad exploratory audits of unrelated code
- specialist security or test-quality review unless the request or risk clearly justifies that extra depth

## Workflow mapping

Consume the same issue taxonomy used by issue-definition and implementation-workflow:

| Issue surface | Issue work type | Primary validation route |
| --- | --- | --- |
| Frontend | Feature / Improvement / Research-backed change | Frontend |
| Backend | Feature / Improvement / Research-backed change | Backend |
| Fullstack | Feature / Improvement / Research-backed change | Fullstack |
| Frontend / Backend / Fullstack | Bugfix | Bugfix depth plus the listed surface |
| Frontend / Backend / Fullstack | Refactor | Refactor depth plus the listed surface |

`Surface` tells you where final proof must land. `Work type` adds bugfix regression depth or refactor behavior-preservation depth on top of the listed surface. `Feature`, `Improvement`, and `Research-backed change` remain issue labels, not standalone validation routes.

## Core Principle

Validate only what the change meaningfully affects, but validate that thoroughly enough to catch likely regressions.

Prefer the smallest relevant final check set first, then expand only when failures, risk, or change scope require it.

Scripts and helpers are optional support, not a substitute for risk-based judgment.

## Workflow

1. Confirm the change is code-complete enough for final validation. If acceptance criteria, scope, or Definition of Done are unclear, stop and use `skills/issue-definition`. If key implementation is still missing, hand back to `skills/implementation-workflow`.
2. Record the incoming `Surface` and `Work type`, then choose the final validation route using the same taxonomy.
3. Choose the smallest sufficient final validation set for the changed surface and risk. Read `references/validation-routing.md` when deciding the route, `references/check-selection.md` when check selection is unclear, and `scripts/select_checks.py` only when repeated or ambiguous check selection would benefit from a helper.
4. Run the selected checks and focused manual verification when needed. Read `references/validation-sequence.md` when you need the full validation order and `references/frontend-verification.md` or `references/backend-verification.md` when the changed surface needs concrete verification guidance.
5. Classify failures. Fix only narrow in-scope validation findings such as broken tests, missing assertions, or small regressions required to complete the promised change. If the failure reveals unfinished implementation or a new scope decision, hand back to `skills/implementation-workflow`.
6. Re-run the relevant checks and report pass/fail status, residual risk, and merge readiness using `assets/validation-report-template.md` by default.

## Validation

Before finalizing:

1. Confirm the executed checks still match the actual changed surface and risk.
2. Re-run every failed-or-fixed check that is needed to prove the final state.
3. Make sure any manual verification you report is specific, reproducible, and tied to the changed behavior.
4. State clearly which acceptance criteria and Definition of Done items were verified, which were not verified, and why.
5. Escalate unresolved out-of-scope failures or missing acceptance criteria instead of silently treating the change as ready.

## Exit criteria

This skill is complete when:
- final checks are selected from the actual changed surface and risk
- acceptance criteria and Definition of Done verification status are explicit
- any fixes applied stayed within validation scope or were handed back for implementation
- residual risk is stated
- merge readiness is clearly reported as ready, ready with noted risk, or not ready

## Support Files

- Use `assets/validation-report-template.md` when writing the final validation summary.
- Read `references/validation-sequence.md` when you need the fuller end-to-end validation sequence.
- Read `references/validation-routing.md` when choosing Frontend, Backend, Fullstack, Bugfix, or Refactor validation depth.
- Read `references/check-selection.md` when selecting the smallest sufficient automated and manual final checks.
- Read `references/failure-handling.md` when a check fails and you need fix-vs-escalate guidance.
- Read `references/frontend-verification.md` when validating frontend behavior, UI states, interaction flows, or accessibility-sensitive changes.
- Read `references/backend-verification.md` when validating backend rules, APIs, persistence, jobs, or integration-heavy changes.
- Read `references/specialist-audit-routing.md` when the request or risk justifies specialist security, performance, or test-quality follow-up.
- Use `scripts/select_checks.py` only when check selection is unclear or repeated enough to benefit from a deterministic helper.

## Edge Cases

- If the request is really asking for implementation cleanup rather than post-change validation, switch to `skills/implementation-workflow` instead of turning this skill into a coding workflow.
- If acceptance criteria or Definition of Done are missing, do not invent them during validation; route to `skills/issue-definition`.
- If broad failures appear outside the changed surface, report them explicitly and avoid silently expanding into an unrelated audit unless the user asks for that depth.
- If the safest proof would require a much broader suite than normal, say so and explain the residual risk when time, tooling, or environment limits prevent running it.
