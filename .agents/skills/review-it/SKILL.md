---
name: review-it
description: Reviews an implementation against its task requirements, acceptance criteria, test coverage, code conventions, security considerations, and observability requirements. Use when the user asks to review, check, validate, or audit an implementation against a task or issue — or says "review this", "check the implementation", "did we cover everything", "validate against the task".
compatibility: Designed for Claude Code. Requires bash for script execution and a git repository for inspecting code changes.
metadata:
  domain: software-review
  version: "1.0"
---

Review an implementation against its task contract.

This skill is task-aware: it reads the related `tasks/issues/` file to extract functional requirements, non-functional requirements, acceptance criteria, observability requirements, and required tests — then evaluates the actual implementation against that structured contract.

Each finding is classified as **Blocking** (prevents mark-complete), **Non-blocking** (should be addressed but does not block), or **Suggestion** (optional improvement).

This skill is read-only. It does not modify source files. It writes only the review report.

## When NOT to use this skill

Do not use review-it when:

- There is no issue or task file — use plan-it to create one first.
- The request is a general open-ended code critique with no task contract to evaluate against — use the built-in `review` skill for PR-level code review instead.
- The implementation has not started — use implement-it first.
- The user is asking how the code works, not whether it satisfies a task.
- The task acceptance criteria are undefined or unresolved.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load the project's domain vocabulary. Use this vocabulary consistently in all finding descriptions and report sections.
2. Identify the issue file to review. Accept it from the user argument, search `tasks/issues/` for the relevant file, or read the most recently modified issue. If no issue file can be identified, stop and ask the user to specify one — do not proceed without a task contract. (See [review-rules.md — Issue identification](references/review-rules.md#issue-identification).)
3. Read the issue file and extract: FRs, NFRs, ACs, OBS requirements, Required Tests, and any ADR dependencies listed under Dependencies.
4. Read the implementation summary in `tasks/implementation/` if one exists for this issue. It records what the implementer believed was done.
5. Inspect the actual code changes using `git diff` against the base branch, or explicit file paths provided by the user. Do not rely solely on the implementation summary — verify against the code. (See [review-rules.md — Code inspection](references/review-rules.md#code-inspection).)
6. Inspect existing project conventions by reading comparable files: similar services, components, tests, or configuration files. Evaluate whether the implementation follows established patterns.
7. Evaluate each acceptance criterion (`AC-*`): determine Pass or Fail based on what the code actually does.
8. Evaluate test coverage: for each required test category in the issue, determine whether matching tests exist and cover the linked requirement IDs.
9. Evaluate observability: for each `OBS-*` requirement, determine whether the implementation includes the required log, metric, trace, or analytics call.
10. Evaluate ADR compliance: if the issue lists ADR files under Dependencies, check whether those ADRs were updated from `Proposed` to `Accepted` or `Rejected` as required by the task's Definition of Done.
11. Classify each finding as **Blocking**, **Non-blocking**, or **Suggestion**. Read [review-rules.md — Finding classification](references/review-rules.md#finding-classification) for the exact criteria.
12. Determine the overall verdict: **Pass** if there are zero Blocking findings; **Fail** if there is one or more.
13. Write the review report in `tasks/reviews/`. Read [output-rules.md](references/output-rules.md) before writing. Use [assets/review-report-template.md](assets/review-report-template.md) as the exact structure.
14. If domain terms were defined or clarified during review, add them to `CONTEXT.md` at the project root using the format in the existing entries.

## Output requirement

When the review is complete, create a review report in `tasks/reviews/`.

Before writing, run:

```bash
mkdir -p tasks/reviews
```

Use this naming format:

```text
tasks/reviews/001-create-project-review.md
tasks/reviews/002-invite-project-member-review.md
```

The numeric prefix matches the related issue number.

## Before marking complete

- [ ] Issue file was read and all FRs, NFRs, ACs, OBS, and Required Tests were extracted
- [ ] Code changes were inspected directly (not only via implementation summary)
- [ ] Every AC is evaluated as Pass or Fail with a concrete reason
- [ ] Every required test category is evaluated as Present or Missing
- [ ] Every Blocking finding references a specific FR, NFR, AC, OBS, or OT ID
- [ ] Overall verdict is **Pass** or **Fail** — no ambiguous or partial verdicts
- [ ] Review report created in `tasks/reviews/` using the template structure
- [ ] No source files were modified

## If output fails

If files cannot be created:
- Verify the directory exists: `ls -ld tasks/reviews/` — if not, run `mkdir -p tasks/reviews`
- Report the error and propose an alternative output location if needed.

## Anti-patterns to avoid

**Summary-only review**: Do not rely on the implementation summary alone. Summaries describe what the implementer believed they did, not what the code actually does. Always inspect the code.

**Vague finding classification**: Do not write Blocking findings without linking a specific requirement or acceptance criterion ID. A finding that says "code quality is poor" is not actionable. A finding that says "AC-003 fails: style inconsistency appears as Blocking, but should be Suggestion per NFR-002" is.

**Blocking inflation**: Do not classify style preferences, naming conventions, or non-contractual improvements as Blocking. Reserve Blocking for failures that directly violate a named FR, NFR, AC, OBS, or security requirement from the issue.

**Requirement invention**: Do not block an implementation for a requirement that is not in the issue. Only evaluate against requirements explicitly stated in the task contract. If you believe a missing requirement is important, raise it as a Suggestion or Non-blocking finding with a recommendation to add it to a follow-up task.

**Silent scope assumption**: If the user provides a file path or diff instead of an issue file, and requirements are ambiguous, flag the ambiguity explicitly in the report under "Unresolved Assumptions" — do not silently invent contract terms.

**ADR over-checking**: Do not flag ADR updates as Blocking unless the task's Definition of Done explicitly required it. If the task said ADRs would be updated and they were not, that is Blocking. If the task's DoD was silent on ADR updates and none were needed, that is not a finding.

## Final response

After writing the review report, summarize:

- issue reviewed
- overall verdict (Pass or Fail)
- count of Blocking, Non-blocking, and Suggestion findings
- ACs that failed, if any
- test categories missing, if any
- ADR compliance status, if relevant
- unresolved assumptions, if any
