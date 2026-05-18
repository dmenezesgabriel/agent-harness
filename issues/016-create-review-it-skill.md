---
id: "016"
created: 2026-05-17
updated: 2026-05-17
status: active
---

# Task: Create review-it skill

## Priority

P0 — Standalone deliverable; no dependency on other open tasks.

## Dependencies

- No task dependency; the `skills/` directory and the plan-it/implement-it conventions already exist.
- No ADR dependency; follows the file-based skill structure already established by plan-it and implement-it.
- Depends on the existing skill directory layout: `SKILL.md`, `assets/`, `references/`, `scripts/`.

## Assignability

**AFK** — all requirements and acceptance criteria are resolved; skill structure is fully specified by plan-it and implement-it as reference patterns; no irreversible architectural decisions remain open.

## Context

The harness ships two complementary skills: `plan-it` (creates structured issue files from a request) and `implement-it` (implements those issues using TDD and existing conventions). A third skill, `review-it`, completes the trilogy by reviewing an implementation against its task requirements, acceptance criteria, test coverage, code conventions, security considerations, and observability requirements.

`review-it` is distinct from the built-in `review` skill (which does general PR review). `review-it` is task-aware: it reads the related `issues/` file to extract FRs, NFRs, ACs, and required tests, then evaluates the implementation against that structured contract.

The skill produces a structured review report in `reviews/`. Each finding is classified as **Blocking** (prevents mark-complete), **Non-blocking** (should be addressed but does not block), or **Suggestion** (improvement for consideration).

## Use Cases

- **Feature**: Task-aware implementation review
- **Scenario**: Developer checks implementation completeness before marking a task done
- **Given** a task exists in `issues/` and code changes are present on the branch
- **When** the developer invokes `review-it`
- **Then** a review report is written in `reviews/` listing which acceptance criteria pass or fail, which required tests are present or missing, and any code quality or security findings

---

- **Feature**: Task-aware implementation review
- **Scenario**: Agent validates its own implementation before claiming completion
- **Given** an agent has completed implement-it for a task
- **When** the agent invokes review-it against the same task
- **Then** the review report surfaces gaps the agent must address before the task can be marked done

## Definition of Ready

- The `skills/` directory exists and follows the plan-it / implement-it structure.
- The `plan-it` SKILL.md and its `assets/` and `references/` are readable as structural patterns.
- The `implement-it` SKILL.md and its `assets/` and `references/` are readable as structural patterns.
- No external dependency or credential is needed to create a skill.

## Functional Requirements

- `FR-001`: The skill reads the related issue file from `issues/` to extract FRs, NFRs, ACs, OBS requirements, and the Required Tests section.
- `FR-002`: The skill inspects actual code changes (via `git diff` or explicit file paths provided by the user) against the issue requirements.
- `FR-003`: The skill evaluates whether each acceptance criterion (`AC-*`) is satisfied by the implementation.
- `FR-004`: The skill evaluates whether each required test category listed in the issue is present and covers the linked requirement.
- `FR-005`: The skill evaluates code changes against existing project conventions (naming, structure, boundaries) discoverable by codebase inspection.
- `FR-006`: The skill evaluates security requirements (`ST-*`) when present in the task.
- `FR-007`: The skill evaluates observability requirements (`OBS-*`, `OT-*`) when present in the task.
- `FR-008`: The skill classifies each finding as **Blocking**, **Non-blocking**, or **Suggestion** with a concrete reason.
- `FR-009`: The skill writes a structured review report in `reviews/` using the review-report template.
- `FR-010`: The skill emits an overall verdict: **Pass** (no blocking findings) or **Fail** (one or more blocking findings).
- `FR-011`: The skill checks whether ADRs were updated when the task required it.

## Non-Functional Requirements

- `NFR-001`: Every finding references the specific `FR-*`, `NFR-*`, `AC-*`, `OBS-*`, or `OT-*` ID it relates to.
- `NFR-002`: The **Blocking** / **Non-blocking** / **Suggestion** classification is unambiguous: Blocking means the task cannot be marked done; Non-blocking means the gap should be fixed but does not block; Suggestion means optional improvement.
- `NFR-003`: The review report follows a consistent template so any engineer can act on it without re-reading the original task.
- `NFR-004`: The skill does not modify source files; it is read-only except for writing the review report.

## Observability Requirements

- `OBS-001`: Not applicable — this task creates a skill definition (Markdown files); there is no runtime to instrument.

## Acceptance Criteria

- `AC-001`: **Given** a task in `issues/` and code changes on the branch, **When** `review-it` is invoked, **Then** a review report file is created in `reviews/` using the naming convention `reviews/NNN-slug-review.md`.
- `AC-002`: **Given** an acceptance criterion in the issue that is not satisfied by the implementation, **When** `review-it` runs, **Then** that AC appears as a **Blocking** finding in the report.
- `AC-003`: **Given** a style inconsistency that does not violate any AC or requirement, **When** `review-it` runs, **Then** it appears as a **Suggestion**, not Blocking.
- `AC-004`: **Given** a required test category listed in the issue that has no corresponding test in the implementation, **When** `review-it` runs, **Then** the missing test category appears as a **Blocking** finding.
- `AC-005`: **Given** all ACs are satisfied and all required tests are present, **When** `review-it` runs, **Then** the overall verdict is **Pass**.
- `AC-006`: **Given** one or more Blocking findings, **When** `review-it` runs, **Then** the overall verdict is **Fail**.
- `AC-007`: **Given** the task has `OBS-*` requirements, **When** `review-it` runs, **Then** the report includes an Observability section confirming whether each OBS requirement was implemented.
- `AC-008`: **Given** no issue file is provided or discoverable, **When** `review-it` is invoked, **Then** the skill prompts the user to specify the issue before proceeding.

## Required Tests

### Unit Tests

- `UT-001`: Not applicable — the skill is defined as Markdown documents; there is no executable unit to isolate.

### Integration Tests

- `IT-001`: Not applicable — same reason as UT-001; skill definitions are not executable code.

### Smoke Tests

- `SMK-001`: **Scenario**: review-it produces a report for a known task/implementation pair  
  **Given** `issues/016-create-review-it-skill.md` exists and the skill files are in place  
  **When** `review-it` is invoked referencing issue 016  
  **Then** a file appears at `reviews/016-create-review-it-skill-review.md` and the overall verdict is present  
  Covers `AC-001`, `AC-005`, `AC-006`.

### End-to-End Tests

- `E2E-001`: Not applicable — skill definitions are Markdown; no browser or user journey applies.

### Regression Tests

- `REG-001`: Not applicable — no prior defect to prevent.

### Performance Tests

- `PT-001`: Not applicable — the skill emits Markdown files; no throughput or latency constraint applies.

### Security Tests

- `ST-001`: Not applicable — the skill is read-only during review; it does not modify source files or execute user input.

### Usability Tests

- `UX-001`: Invoke `review-it` on a task with one passing AC and one failing AC, then verify the report is clear enough for a human reviewer to act on without re-reading the original issue. Covers `NFR-003`.

### Observability Tests

- `OT-001`: Not applicable — no runtime instrumentation in a skill definition.

## Definition of Done

- `skills/review-it/SKILL.md` exists and follows the plan-it/implement-it SKILL.md structure with correct YAML frontmatter, a "When NOT to use" section, a numbered core workflow, output requirements, a "Before marking complete" checklist, anti-patterns, and a final response section.
- `skills/review-it/assets/review-report-template.md` exists and covers: related task, overall verdict, findings table (Blocking/Non-blocking/Suggestion with linked IDs), AC evaluation, test coverage evaluation, observability evaluation, ADR compliance, convention notes, and unresolved follow-up.
- `skills/review-it/references/review-rules.md` exists and defines how to classify findings, how to inspect code, and how to handle tasks with no issue file.
- `skills/review-it/references/output-rules.md` exists and defines the `reviews/` directory, file naming, template usage, and final response format.
- `skills/review-it/scripts/ensure-reviews-dir.sh` exists and creates the `reviews/` directory if absent.
- All required files are present and internally consistent (SKILL.md references the asset and reference paths that actually exist).
- Smoke test `SMK-001` passes manually.
- No source files are modified as a side effect of creating the skill.
