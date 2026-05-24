---
id: "023"
created: 2026-05-23
updated: 2026-05-23
status: active
---

# Task: Skill self-containment and token efficiency

## Priority

P0 — Blocking correct isolated use of each skill; agents reading one skill must not encounter references to another skill or to issues that may no longer exist.

## Dependencies

- No task dependency; all source files are readable now.
- No ADR dependency; these are documentation-only edits with no architectural decisions.

## Assignability

**AFK** — all changes are enumerated and localized; no irreversible decisions remain open.

## Context

Three skills — `plan-it`, `implement-it`, `review-it` — must each work independently when loaded by an agent. Currently they have three categories of cross-contamination:

1. **ADR → issue links**: `plan-it/assets/adr-template.md` has a "Related Tasks" section that links ADRs to issue files. ADRs are long-lived repository artifacts; issues are cleaned up periodically. An ADR that links to a deleted issue contains a broken pointer. The fix removes the section from the template and removes the corresponding guidance from `adr-rules.md`.

2. **Cross-skill name references**: `implement-it/SKILL.md` and `review-it/SKILL.md` name other skills in their "When NOT to use" sections. This forces an agent loading only one skill to know about the others. The fix replaces skill names with generic task-state descriptions.

3. **Skill names in context-template.md**: All three copies of `context-template.md` say "Both plan-it and implement-it read it at session start." This text ends up in every project's `CONTEXT.md`, coupling the generated file to specific skill names. The fix makes the description generic.

Additionally, the "Output requirement" / "Output files" sections in all three `SKILL.md` files include inline example file paths that duplicate what `output-files.md` (plan-it) and `output-rules.md` (implement-it, review-it) already define. Replacing them with a pointer saves tokens on every skill invocation.

After source edits, `scripts/install-skills.sh` must be run to propagate changes to `.agents/skills/`.

## Use Cases

- **Feature**: Isolated skill invocation
- **Scenario**: Agent loads only implement-it
- **Given** an agent has access only to `skills/implement-it/SKILL.md` and its references
- **When** it reads the "When NOT to use" section
- **Then** it sees no reference to another skill by name

- **Feature**: ADR long-term viability
- **Scenario**: Maintainer deletes completed issues
- **Given** old issue files have been removed
- **When** a maintainer reads an ADR in `docs/adrs/`
- **Then** the ADR contains no broken links to deleted issue files

## Definition of Ready

- All source files listed in Functional Requirements are readable at their stated paths.
- `scripts/install-skills.sh` is executable and installs to `.agents/skills/`.

## Functional Requirements

- `FR-001`: `skills/plan-it/assets/adr-template.md` must not contain a "Related Tasks" section.
- `FR-002`: `skills/plan-it/references/adr-rules.md` must not instruct agents to link ADRs back to task files.
- `FR-003`: `skills/implement-it/SKILL.md` "When NOT to use" must not name another skill.
- `FR-004`: `skills/review-it/SKILL.md` "When NOT to use" must not name another skill.
- `FR-005`: All three `context-template.md` files (`plan-it`, `implement-it`, `review-it`) must not name any specific skill in their description line.
- `FR-006`: `skills/plan-it/SKILL.md` "Issue output requirement" and "ADR output requirement" sections must be condensed to a single "Output files" section that keeps the `mkdir` guards and points to `references/output-files.md` for naming rules.
- `FR-007`: `skills/review-it/SKILL.md` "Output requirement" section must keep the `mkdir` guard and point to `references/output-rules.md`.
- `FR-008`: `skills/implement-it/SKILL.md` "Output requirement" section must keep the `mkdir` guard and point to `references/output-rules.md`.
- `FR-009`: After all source edits, `scripts/install-skills.sh` must be run to sync changes to `.agents/skills/`.

## Non-Functional Requirements

- `NFR-001`: No wording change may make an instruction vague; each replacement must remain unambiguous.
- `NFR-002`: The condensed output sections must preserve the `mkdir -p` commands verbatim.
- `NFR-003`: Changes to `adr-rules.md` must preserve the one-way task → ADR linking rule (tasks reference ADRs; the reverse is removed).

## Observability Requirements

- Not applicable — no runtime components are involved; all changes are to Markdown files.

## Acceptance Criteria

- `AC-001`: **Given** `skills/plan-it/assets/adr-template.md` is read, **When** searching for "Related Tasks", **Then** the section is not found.
- `AC-002`: **Given** `skills/plan-it/references/adr-rules.md` is read, **When** searching for "ADR references the related task file" or "Link the ADR to affected task files", **Then** neither phrase is found.
- `AC-003`: **Given** `skills/implement-it/SKILL.md` is read, **When** searching for any other skill name (plan-it, review-it), **Then** none are found outside the frontmatter.
- `AC-004`: **Given** `skills/review-it/SKILL.md` is read, **When** searching for any other skill name (plan-it, implement-it), **Then** none are found outside the frontmatter.
- `AC-005`: **Given** any of the three `context-template.md` files is read, **When** searching for "plan-it" or "implement-it" in the description line, **Then** neither is found.
- `AC-006`: **Given** `skills/plan-it/SKILL.md` is read, **When** searching for "Issue output requirement" or "ADR output requirement" as section headings, **Then** neither is present; a single "Output files" section exists instead.
- `AC-007`: **Given** the condensed output sections, **When** verifying `mkdir -p` guards, **Then** each guard is present and correct.
- `AC-008`: **Given** `scripts/install-skills.sh` is run after source edits, **When** inspecting `.agents/skills/implement-it/SKILL.md`, **Then** it matches the updated source.

## Required Tests

### Unit Tests

- Not applicable — all changes are to Markdown files; no executable logic exists.

### Integration Tests

- Not applicable — no system boundaries crossed.

### Smoke Tests

- `SMK-001`: **Scenario**: Verify no cross-skill name in implement-it  
  **Given** the source edits are complete  
  **When** running `grep -n "plan-it\|review-it" skills/implement-it/SKILL.md`  
  **Then** output contains only the `name:` frontmatter line (self-reference), no other matches.

- `SMK-002`: **Scenario**: Verify no cross-skill name in review-it  
  **Given** the source edits are complete  
  **When** running `grep -n "plan-it\|implement-it" skills/review-it/SKILL.md`  
  **Then** output contains only the `name:` frontmatter line, no other matches.

- `SMK-003`: **Scenario**: Verify ADR template has no Related Tasks  
  **Given** the source edits are complete  
  **When** running `grep -n "Related Tasks" skills/plan-it/assets/adr-template.md`  
  **Then** no output.

- `SMK-004`: **Scenario**: Installed implement-it matches source  
  **Given** `scripts/install-skills.sh` was run  
  **When** running `diff skills/implement-it/SKILL.md .agents/skills/implement-it/SKILL.md`  
  **Then** no diff output.

### End-to-End Tests

- Not applicable — no user-facing application.

### Regression Tests

- Not applicable — no prior defect being guarded.

### Performance Tests

- Not applicable — no runtime behavior.

### Security Tests

- Not applicable — no trust boundaries involved.

### Usability Tests

- Not applicable — no interactive UI.

### Observability Tests

- Not applicable — no logs, metrics, or traces involved.

## Definition of Done

- All eight source files are edited as specified in Functional Requirements.
- `scripts/install-skills.sh` has been run and `.agents/skills/` matches source.
- SMK-001 through SMK-004 pass.
- No other skill files were modified.
