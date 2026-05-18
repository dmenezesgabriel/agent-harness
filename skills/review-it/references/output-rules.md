# Output Rules

After completing the review, write a review report in `reviews/`.

## Directory rule

Before writing the review report, ensure the directory exists:

```bash
mkdir -p reviews
```

## File rules

- Use the same numeric prefix as the related issue.
- Use a short descriptive lowercase slug matching the issue slug.
- Append `-review` to the slug.
- Use kebab-case.
- Use `.md` extension.
- Keep one review report per reviewed issue.
- Set `id` in the frontmatter to the numeric prefix used in the filename.
- Set `issue` in the frontmatter to the path of the related issue file.
- Set `created` to today's date (YYYY-MM-DD) when first writing the file.
- Set `updated` to today's date (YYYY-MM-DD) each time the file is modified.
- Use `assets/review-report-template.md` as the required structure.

## File naming format

```text
reviews/001-short-descriptive-slug-review.md
```

Good:
- `reviews/001-create-project-review.md`
- `reviews/002-invite-project-member-review.md`
- `reviews/016-create-review-it-skill-review.md`

Bad:
- `reviews/done.md`
- `reviews/review1.md`
- `reviews/task-review final.md`
- `reviews/001.md`
- `reviews/Review.md`

## Report content

The report must include:

- related issue file path
- overall verdict (Pass or Fail) with Blocking finding IDs if Fail
- findings table: ID, level, related requirement ID, description, evidence
- AC evaluation: one row per AC, Pass or Fail with reason
- test coverage evaluation: one row per required test category, Present or Missing
- observability evaluation: one row per OBS requirement (skip if all are Not applicable)
- ADR compliance: status of each ADR dependency (skip if none listed)
- convention notes: any Non-blocking or Suggestion findings from convention evaluation
- unresolved assumptions or follow-up work

Good:
- `F-001 — Blocking — AC-004 — unit test category missing; no test file found for UT-001.`
- `AC-001: Pass — review report file created at reviews/016-create-review-it-skill-review.md.`
- `UT-001: Missing — no file matching the test described in the Required Tests section was found.`

Bad:
- Done.
- Looks good.
- Tests pass.
- Code is fine.

## Final response after file generation

After writing the review report, summarize in the conversation:

- which issue was reviewed
- overall verdict
- count of Blocking, Non-blocking, and Suggestion findings
- names of failing ACs, if any
- test categories marked Missing, if any
- ADR compliance status, if relevant
- unresolved assumptions, if any

Good:
- Reviewed `issues/016-create-review-it-skill.md`. Verdict: **Pass**. 0 Blocking, 1 Non-blocking, 2 Suggestions.
- Reviewed `issues/001-create-project.md`. Verdict: **Fail** (F-001, F-003). AC-002 fails, IT-001 missing.

Bad:
- Done.
- Review complete.
- No issues found.
