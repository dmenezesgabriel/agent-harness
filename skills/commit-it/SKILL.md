---
name: commit-it
description: Groups changed files into atomic logical units and commits each with a Conventional Commits message. Use when the user says "commit this", "create a commit", "make atomic commits", "semantic commit", or "ship this".
compatibility: Requires git. Designed for Claude Code.
metadata:
  domain: version-control
  version: "1.0"
---

Commit all working-tree changes as one or more atomic commits with Conventional Commits messages.

## When NOT to use this skill

Do not use commit-it when:

- The working tree is clean — nothing to commit.
- The user has not reviewed the changes — suggest `review-it` first.
- The user wants to amend, squash, or rebase existing commits — those are manual git operations.
- The user wants a dry-run or preview only — describe what you would commit without staging.

## Core workflow

1. If a `tasks/issues/` file is referenced or present for the current work, read it for domain vocabulary and scope context.
2. Inspect the working tree:
   ```bash
   git status
   git diff HEAD
   ```
3. Group all changed files into atomic logical units. One unit = one concern. Read [commit-rules.md — Atomicity](references/commit-rules.md#atomicity) for grouping criteria.
4. For each unit in dependency order:
   - Stage only the files in that unit — never `git add .` or `git add -A`:
     ```bash
     git add <file1> <file2> ...
     ```
   - Generate a Conventional Commits message per [commit-rules.md — Message format](references/commit-rules.md#message-format).
   - Commit:
     ```bash
     git commit -m "<type>(<scope>): <description>"
     ```
   - If a pre-commit hook fails: fix the root cause, re-stage, retry. Never use `--no-verify`.
5. Verify:
   ```bash
   git log --oneline -5
   ```

## Gotchas

- **Never `git add .` or `git add -A`** — this bundles unrelated changes and defeats atomicity.
- **Refuse to commit secrets**: `.env`, credential files, API keys, tokens. Warn the user and skip those files.
- **Lock files and generated files** belong with the source change that triggered them — not in a separate commit.
- **Breaking changes** require a `BREAKING CHANGE:` footer. Read [commit-rules.md — Breaking changes](references/commit-rules.md#breaking-changes).
- **Pre-commit hooks are not optional** — if one fails, fix the underlying issue rather than bypassing it.
- **Do not commit files with conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`). Stop and tell the user.

## Final response

After all commits, report:

- each commit hash and message from `git log --oneline`
- files skipped and why
- unresolved issues (hook failures, conflict markers, secret candidates)
