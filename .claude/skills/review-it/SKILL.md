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

Each finding is classified as **Blocking** (violates a named FR/AC/NFR/OBS/security requirement from the issue), **Non-blocking** (gap that should be addressed but does not prevent completion), or **Suggestion** (optional improvement, never blocks). See [review-rules.md — Finding classification](references/review-rules.md#finding-classification) for exact criteria.

This skill is read-only. It does not modify source files. It writes only the review report.

## When NOT to use this skill

Do not use review-it when:

- There is no issue or task file — create one first.
- The request is a general open-ended code critique with no task contract to evaluate against — use a PR-level code review instead.
- The implementation has not started — complete it first.
- The user is asking how the code works, not whether it satisfies a task.
- The task acceptance criteria are undefined or unresolved.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load the project's domain vocabulary. Use this vocabulary consistently in all finding descriptions and report sections.
2. Identify the issue file to review. Accept it from the user argument, search `tasks/issues/` for the relevant file, or read the most recently modified issue. If no issue file can be identified, stop and ask the user to specify one — do not proceed without a task contract. (See [review-rules.md — Issue identification](references/review-rules.md#issue-identification).)
3. Read the issue file and extract: FRs, NFRs, ACs, OBS requirements, Required Tests, and any ADR dependencies listed under Dependencies.
4. Read the implementation summary in `tasks/implementation/` if one exists for this issue. It records what the implementer believed was done.
5. Inspect the actual code changes using `git diff` against the base branch, or explicit file paths provided by the user. Do not rely solely on the implementation summary — verify against the code. (See [review-rules.md — Code inspection](references/review-rules.md#code-inspection).) Implementation sessions are subject to attention pressure: a requirement that was read early in the session may have been silently dropped rather than consciously descoped. Treat a requirement that is absent from the code as a candidate finding to be classified — not a silent pass.
6. Inspect project conventions by reading comparable files (similar services, components, tests). Flag generic names (`data`, `handler`, `result`, `item`, `Manager`) as Non-blocking. For typed languages, flag missing type annotations on new/modified public signatures as Non-blocking. Both are Non-blocking unless an AC explicitly required otherwise.
7. Evaluate each `AC-*`: restate it, inspect the code for evidence, mark **Pass** or **Fail**. Never mark Pass without code evidence; never mark Fail without code evidence. If Fail, add a Blocking finding with the AC ID and a concrete description of what is missing.
8. Evaluate test coverage: for each required test category in the issue, determine whether matching tests exist and cover the linked requirement IDs.
9. Evaluate observability: for each `OBS-*` requirement, determine whether the implementation includes the required log, metric, trace, or analytics call.
10. Evaluate ADR compliance: if the issue lists ADR files under Dependencies, check whether those ADRs were updated from `Proposed` to `Accepted` or `Rejected` as required by the task's Definition of Done.
11. Classify each finding as **Blocking**, **Non-blocking**, or **Suggestion**. Read [review-rules.md — Finding classification](references/review-rules.md#finding-classification) for the exact criteria.
12. Determine the overall verdict: **Pass** if there are zero Blocking findings; **Fail** if there is one or more.
13. Write the review report in `tasks/reviews/`. Read [output-rules.md](references/output-rules.md) before writing. Use [assets/review-report-template.md](assets/review-report-template.md) as the exact structure.
14. If domain terms were defined or clarified during review, add them to `CONTEXT.md` at the project root using the format in the existing entries.

## Output files

Create one review report in `tasks/reviews/` when the review is complete.

```bash
mkdir -p tasks/reviews
```

See [output-rules.md](references/output-rules.md) for naming, numbering, and report structure.

## Before marking complete

- [ ] No source files were modified — this skill is read-only.

## If output fails

If files cannot be created:
- Verify the directory exists: `ls -ld tasks/reviews/` — if not, run `mkdir -p tasks/reviews`
- Report the error and propose an alternative output location if needed.

## Anti-patterns to avoid

**Code-driven, contract-bound**: Always inspect the actual code — not the implementation summary. Evaluate only against named FR/AC/NFR/OBS/security requirements in the issue. Link every Blocking finding to a specific requirement ID. Flag ambiguities explicitly under "Unresolved Assumptions" — never invent contract terms.

**Right-sized findings**: Reserve Blocking for requirement violations only. Style preferences, naming conventions, and non-contractual improvements are Non-blocking or Suggestion. ADR updates are Blocking only when the task's Definition of Done explicitly required them.

## Final response

After writing the review report, summarize as specified in [output-rules.md — Final response](references/output-rules.md#final-response-after-file-generation).
