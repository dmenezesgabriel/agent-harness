---
name: change-validation
description: Use this skill when you need to validate a completed change, run the smallest relevant checks, fix failing tests or regressions, confirm acceptance criteria or Definition of Done, and verify readiness before merge. Do not use for initial issue framing or broad exploratory audits of unrelated code.
---

## Purpose

Validate a defined code change after implementation by confirming scope, acceptance criteria, and relevant quality gates.

Run the smallest relevant verification set, investigate failures, fix in-scope regressions, and report pass/fail status, residual risk, and readiness.

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

Use this skill for targeted post-implementation verification and correction of a defined change.

Do not use it for:
- initial issue framing or solution design
- broad exploratory audits of unrelated code
- specialist security or test-quality review unless the request or risk clearly justifies that extra depth

## Core Principle

Validate only what the change meaningfully affects, but validate that thoroughly enough to catch likely regressions.

Prefer the smallest relevant check set first, then expand only when failures, risk, or change scope require it.

Scripts and helpers are optional support, not a substitute for risk-based judgment.

## Short Validation Flow

1. Confirm the exact change scope, acceptance criteria, constraints, and non-goals.
2. Identify affected surfaces and choose the smallest sufficient validation set.
3. Run the selected checks and focused manual verification when needed.
4. Classify failures, fix in-scope regressions, and add regression coverage when required.
5. Re-run the relevant checks and summarize status, residual risk, and readiness.

Use these references when you need more detail:
- `references/validation-sequence.md`
- `references/validation-routing.md`
- `references/check-selection.md`
- `references/failure-handling.md`

## Validation Boundaries

Keep validation proportional to the changed surface and risk.

Usually include only the checks needed to prove the changed behavior is correct.
Expand to higher-level checks, broader regression coverage, or specialist audits only when the change crosses that boundary or the risk justifies it.

Use the implementation-workflow route terms consistently while validating: Frontend, Backend, Fullstack, Bugfix, and Refactor.

For surface-specific verification, use:
- `references/frontend-verification.md`
- `references/backend-verification.md`
- `references/specialist-audit-routing.md`

## Assets, Scripts, and References

Default report structure:
- `assets/validation-report-template.md`

Optional helper:
- `scripts/select_checks.py` for unclear or repeated check selection work

Reference files:
- `references/validation-sequence.md`
- `references/validation-routing.md`
- `references/check-selection.md`
- `references/failure-handling.md`
- `references/frontend-verification.md`
- `references/backend-verification.md`
- `references/specialist-audit-routing.md`
