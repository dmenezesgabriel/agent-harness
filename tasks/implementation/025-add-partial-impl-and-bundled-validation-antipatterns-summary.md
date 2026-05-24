---
task: "025"
date: 2026-05-23
---

# Implementation Summary — Task 025

## Files changed

- `skills/plan-it/SKILL.md` — added two anti-pattern entries to "Anti-patterns to avoid" section
- `.agents/skills/plan-it/SKILL.md` — propagated via `scripts/install-skills.sh` (symlink; matches source)

## Behavior implemented

- **FR-001**: "Partial implementations" anti-pattern added — agents are told not to create tasks that leave the system broken pending a follow-up task.
- **FR-002**: "Bundled change and validation" anti-pattern added — agents are told not to combine code/text changes with benchmark or promotion steps in the same task.
- **FR-003**: Both entries use the bold-heading + prose format consistent with existing anti-patterns.
- **FR-004**: `scripts/install-skills.sh` was run; `.agents/skills/plan-it/SKILL.md` matches source (no diff).

## Tests

No executable tests apply — changes are pure Markdown.

- SMK-001: `grep -n "Partial implementations" skills/plan-it/SKILL.md` → line 81 found.
- SMK-002: `grep -n "Bundled change and validation" skills/plan-it/SKILL.md` → line 83 found.
- SMK-003: `diff skills/plan-it/SKILL.md .agents/skills/plan-it/SKILL.md` → no output.

## Intentionally not applicable

Unit, integration, E2E, regression, performance, security, usability, and observability tests — no executable logic; changes are Markdown only.
