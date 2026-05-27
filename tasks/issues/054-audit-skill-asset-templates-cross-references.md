---
id: "054"
created: 2026-05-26
updated: 2026-05-26
status: active
---

# Task: Audit skill asset templates for cross-skill references and fix any found

## Priority

P3 — The three Skills (plan-it, implement-it, review-it) are designed to be usable independently. If the output file templates contain field labels or section headers that reference another Skill's output by name, they create implicit coupling that breaks standalone use.

## Dependencies

- No task dependency; no ADR dependency.
- Requires read access to all `assets/` template files across the three Skill directories.

## Assignability

**AFK** — this is a read-then-fix task with no open architectural decisions. The fix is renaming any cross-referencing label to a neutral equivalent.

## Context

The three Skills write their outputs to different directories:
- `tasks/issues/` — task files
- `tasks/implementation/` — implementation summaries
- `tasks/reviews/` — review reports

Each Skill has asset templates in its `assets/` directory that define the exact structure of output files. If any template field, section header, or label explicitly names another Skill (e.g., "Plan-it task file:", "Implement-it summary:", or "Review-it report:"), the output file generated from that template is coupled to the assumption that a specific other Skill was used. This breaks standalone use: a user who writes a task file by hand, or who uses only the review Skill against an existing codebase, will produce output that does not conform to the expected field name.

This task reads all template files across the three Skill directories, identifies any cross-skill references (Skill names, Skill-specific output directory names used as labels, or assumption of another Skill's presence), and renames them to neutral, generic labels.

Skill directories:
- `skills/plan-it/assets/`
- `skills/review-it/assets/`
- `.pi/skills/implement-it/assets/`

## Use Cases

- **Feature**: Skill-agnostic output templates
- **Scenario**: User writes a task file by hand (without using plan-it) and then runs the review Skill
- **Given** the review template has no cross-skill references
- **When** the reviewer reads the task file and writes a review
- **Then** the review report structure is identical to one produced after a plan-it session

- **Scenario**: Developer reads an implementation summary written without the implement-it Skill
- **Given** the implementation summary template uses neutral labels
- **When** the developer reads the summary
- **Then** no section implies that a specific Skill was required to produce it

## Definition of Ready

- All three Skill `assets/` directories are readable.
- The list of Skill names that must not appear in template labels is: `plan-it`, `implement-it`, `review-it`.

## Functional Requirements

- `FR-001`: All template files in `skills/plan-it/assets/`, `skills/review-it/assets/`, and `.pi/skills/implement-it/assets/` are read and inspected for cross-skill references.
- `FR-002`: Any field label, section header, or descriptive text in a template that references another Skill by name is renamed to a neutral, generic label that does not imply a specific Skill.
- `FR-003`: References to output directory paths (`tasks/issues/`, `tasks/implementation/`, `tasks/reviews/`) used as field labels (rather than as file paths) are also made neutral if they imply a specific Skill's presence.
- `FR-004`: If no cross-skill references are found in a template file, that file is not modified.
- `FR-005`: A summary of findings is produced listing: each file inspected, each reference found (if any), and the neutral label replacement used.

## Non-Functional Requirements

- `NFR-001`: Only template files are modified — SKILL.md files and reference files are not touched by this task.
- `NFR-002`: Renaming preserves the section's meaning and does not reduce the template's utility.

## Observability Requirements

Not applicable — this task reads and potentially edits Markdown template files with no runtime telemetry.

## Acceptance Criteria

- `AC-001`: **Given** all template files are inspected, **When** any cross-skill reference is found, **Then** it is renamed to a neutral label.
- `AC-002`: **Given** the final state of all template files, **When** each file is read, **Then** none contains the strings `plan-it`, `implement-it`, or `review-it` in field labels or section headers (file paths in comments are acceptable).
- `AC-003`: **Given** the task is complete, **When** the summary of findings is read, **Then** every inspected file is listed with its finding status (references found and fixed, or no references found).
- `AC-004`: **Given** the final state of all template files, **When** they are read, **Then** each template remains structurally complete (no section removed, only labels changed).

## Required Tests

### Unit Tests

Not applicable — this task inspects and edits Markdown template files, not executable code.

### Integration Tests

Not applicable — no executable integration boundary exists in this change.

### Smoke Tests

- `SMK-001`: **Scenario**: All template files are readable and no cross-skill references remain  
  **Given** all template files have been inspected and fixed  
  **When** each file is read  
  **Then** none contains `plan-it`, `implement-it`, or `review-it` in field labels or section headers  
  Covers `AC-002`.

### End-to-End Tests

Not applicable — no complete user journey changes; this is a template file audit.

### Regression Tests

Not applicable — no known previous defect specific to this text edit.

### Performance Tests

Not applicable — text-only change with no runtime performance impact.

### Security Tests

Not applicable — no authentication, authorization, or trust boundary is touched.

### Usability Tests

Not applicable — these are output template files, not a user interface.

### Observability Tests

Not applicable — this task does not introduce or modify operationally observable behavior.

## Definition of Done

- All template files in `skills/plan-it/assets/`, `skills/review-it/assets/`, and `.pi/skills/implement-it/assets/` have been read.
- Any cross-skill references in field labels or section headers are renamed to neutral equivalents.
- A summary of findings is produced.
- No template file was reduced in structure — only labels were changed.
