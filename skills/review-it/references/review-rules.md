# Review Rules

Use these rules to evaluate implementations against their task contracts precisely, without inventing requirements or inflating findings.

## Issue identification

Before reviewing, identify the issue file that defines the task contract.

Resolution order:

1. Accept the issue file path from the user argument (e.g., `@issues/016-create-review-it-skill.md`).
2. If no argument is given, search `issues/` for the most recently modified active issue.
3. If multiple candidates exist, ask the user to choose one — do not guess.
4. If no issue file can be identified, stop and ask the user to specify one. Do not proceed without a task contract.

Good:
- User provides `@issues/016-create-review-it-skill.md` → read that file.
- User says "review the latest task" → read the most recently modified active issue.
- User says "review" with no context and three issues are active → ask which one.

Bad:
- Invent requirements when no issue file is found.
- Proceed with a guess when multiple candidates exist.
- Review a PR diff without extracting the task contract from the issue.

## Code inspection

Always inspect the actual code changes, not only the implementation summary.

Implementation summaries describe what the implementer believed they did. They may be incomplete or inaccurate.

How to inspect:

1. Run `git diff <base-branch>...HEAD` to see all changes since the branch diverged from the base.
2. If the user specifies explicit file paths, read those files directly.
3. If no base branch is obvious, try `git diff main...HEAD`, then `git diff master...HEAD`, then `git log --oneline -10` to find the branch point.
4. Read the actual test files, not just file names listed in the summary.

Good:
- Run `git diff main...HEAD` and read the output before evaluating any AC.
- Read `tests/unit/project-name.test.ts` to verify what the unit test actually asserts.
- Compare the implementation file against the AC to verify behavior.

Bad:
- Evaluate ACs by reading only the implementation summary.
- Assume a test exists because the summary claims it does without checking the file.
- Treat `git status` output as a substitute for reading changed files.

## Finding classification

Every finding must be classified as one of three levels.

### Blocking

Use Blocking when the implementation directly violates a named requirement or acceptance criterion in the issue.

Criteria for Blocking:
- An `AC-*` criterion is not satisfied by the code.
- A `FR-*` functional requirement is not implemented.
- A required test category listed in the issue is entirely absent.
- A security requirement (`ST-*`) is violated.
- A `NFR-*` constraint is provably broken (e.g., the API returns a different error format than specified).
- An `OBS-*` requirement is missing and the issue required it.
- The task's Definition of Done required ADR updates that were not made.
- The skill is read-only per `NFR-004` but source files were modified.

Every Blocking finding must reference the specific ID it violates.

Good:
- Blocking: `AC-004` — the required test for unit tests is absent; `issues/016` Required Tests lists `UT-001` but no matching test file exists.
- Blocking: `FR-009` — no review report is written to `reviews/`; the skill invocation produced no output file.

Bad:
- Blocking: code is messy.
- Blocking: naming could be better.
- Blocking: needs more comments.

### Non-blocking

Use Non-blocking when the implementation has a gap that should be addressed but does not prevent the task from being marked done.

Criteria for Non-blocking:
- A `NFR-*` or `OBS-*` requirement is partially implemented (e.g., a log line exists but is missing one field).
- An edge case mentioned in the issue context is not handled, but no AC or FR explicitly required it.
- An existing test is present but does not cover the linked requirement ID it claims to cover.
- A convention is inconsistently applied in one place but correct everywhere else.

Every Non-blocking finding must reference the relevant ID and describe the gap precisely.

Good:
- Non-blocking: `OBS-001` — log line exists but is missing `requestId`; the OBS requirement listed `requestId` as required.
- Non-blocking: `UT-001` — test exists but does not assert the 80-character boundary; `FR-002` specifies this limit explicitly.

Bad:
- Non-blocking: test could be better.
- Non-blocking: probably fine but could be improved.

### Suggestion

Use Suggestion for improvements that are not required by the task contract.

Criteria for Suggestion:
- A style choice differs from project convention but does not violate any named requirement.
- A code structure could be simplified without changing behavior.
- An alternative approach might be clearer, but the current one satisfies all requirements.
- A future risk exists that is not in scope for this task.

Suggestions must not block the task from being marked done.

Good:
- Suggestion: `ensure-reviews-dir.sh` follows the same pattern as `ensure-issues-dir.sh` but could DRY the mkdir logic — not required by the task.
- Suggestion: variable name `r` in `review-rules.md` line 12 could be more descriptive — style preference, not a requirement.

Bad:
- Suggestion (that is actually Blocking): AC-002 is not satisfied — classify as Blocking.
- Suggestion: everything is fine — this adds no value.

## AC evaluation

For each `AC-*` in the issue:

1. Restate the AC.
2. Inspect the code to determine whether the AC is satisfied.
3. Mark it **Pass** or **Fail**.
4. If Fail, add a Blocking finding with the AC ID and a concrete description of what is missing.

Do not mark an AC as Pass without evidence from the code.
Do not mark an AC as Fail without evidence from the code.

## Test coverage evaluation

For each test category in the issue's Required Tests section:

1. If the issue marks a category as `Not applicable — <reason>`, skip it.
2. If the issue defines tests (e.g., `UT-001`, `IT-001`), verify each exists in the codebase.
3. Check that the test actually asserts the behavior or covers the ID it claims to cover — not just that the file exists.
4. If a required test is missing entirely, add a Blocking finding.
5. If a test exists but does not cover the linked ID fully, add a Non-blocking finding.

Good:
- `UT-001` required by the issue → read `tests/unit/project-name.test.ts` → verify it tests 1–80 character names → Pass.
- `IT-001` required by the issue → no integration test file found → Blocking.

Bad:
- Mark `UT-001` as Present because the implementation summary says it was added.
- Skip test evaluation because "tests are probably fine."

## Observability evaluation

For each `OBS-*` requirement in the issue:

1. If marked `Not applicable`, skip it.
2. Read the relevant implementation file.
3. Verify the log, metric, trace, or analytics call exists and includes every field specified.
4. If the requirement is entirely missing, add a Blocking finding.
5. If the requirement is partially implemented (e.g., missing one field), add a Non-blocking finding.

## ADR compliance evaluation

Check ADR compliance only when the issue explicitly lists ADR files under Dependencies or requires ADR updates in its Definition of Done.

1. Read the issue's Dependencies section.
2. If ADR files are listed, check whether they exist and whether their status was updated from `Proposed`.
3. If the Definition of Done required ADR updates and they were not made, add a Blocking finding.
4. If the task did not require ADR updates, do not create a finding about ADRs.

## Convention evaluation

To evaluate code conventions:

1. Identify existing comparable files: similar services, handlers, tests, or components in the codebase.
2. Compare naming, file structure, boundary placement, and import order.
3. Classify significant deviations as Non-blocking when they affect readability or consistency.
4. Classify minor style preferences as Suggestion.
5. Do not classify convention deviations as Blocking unless they violate a named NFR or task requirement.

## Finding IDs

Assign a stable ID to each finding for traceability.

Format: `F-NNN` starting at `F-001` per report.

Each finding must include:
- ID (`F-001`)
- Level (Blocking / Non-blocking / Suggestion)
- Related requirement ID (`AC-001`, `FR-002`, `OBS-001`, etc.)
- Description (what is wrong or could be improved)
- Evidence (file path or git diff line where the gap was observed)

Good:
- `F-001` — **Blocking** — `AC-002` — The failing AC is not surfaced as Blocking in the report; `skills/review-it/SKILL.md` line 38 classifies it as Suggestion instead.
- `F-002` — **Non-blocking** — `OBS-001` — Log line at `src/api/project.ts:42` is missing `requestId`.
- `F-003` — **Suggestion** — (no ID) — Variable `r` at `src/service/review.ts:8` could be named `report` for clarity.

## Overall verdict

**Pass**: zero Blocking findings.
**Fail**: one or more Blocking findings.

Do not use any other verdict. Do not use "Partial", "Conditional", or "Pending review".

If the verdict is Fail, list the Blocking finding IDs in the verdict line so the implementer knows exactly what to fix.
