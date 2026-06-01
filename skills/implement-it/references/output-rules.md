# Output Rules

Write a short implementation summary in `tasks/implementation/` after each task.

## Directory rule

Before writing implementation output, ensure the directory exists:

```bash
mkdir -p tasks/implementation
```

## File rules

- Use the same numeric prefix as the related issue when possible.
- Use a short descriptive lowercase slug.
- Use kebab-case for slugs.
- Use `.md` extension.
- Keep one implementation summary per implemented issue or task.
- Set `id` in the frontmatter to the numeric prefix used in the filename.
- Set `issue` in the frontmatter to the path of the related issue file.
- Set `created` to today's date (YYYY-MM-DD) when first writing the file.
- Set `updated` to today's date (YYYY-MM-DD) each time the file is modified.
- Use `assets/implementation-summary-template.md`.

## File naming format

```text
tasks/implementation/001-short-descriptive-slug-summary.md
```

Good:
- `tasks/implementation/001-create-project-summary.md`
- `tasks/implementation/002-invite-project-member-summary.md`
- `tasks/implementation/003-protect-project-settings-summary.md`

Bad:
- `tasks/implementation/done.md`
- `tasks/implementation/task1.md`
- `tasks/implementation/summary final.md`
- `tasks/implementation/001.md`

## Summary content

The summary must include:

- task implemented
- files changed
- behavior implemented
- design notes
- tests added or updated
- validations run
- ADRs updated
- observability added or changed
- skipped or not-applicable test categories
- unresolved assumptions or follow-up work

Good:
- `UT-001` added for project name length.
- `IT-001` added for `POST /projects` persistence.
- `E2E-001` not applicable — this task changed only a pure validator.

Bad:
- Done.
- Tests passed.
- No issues.
