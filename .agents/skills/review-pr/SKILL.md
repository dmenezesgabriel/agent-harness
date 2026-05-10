---
name: review-pr
description: Review pull requests for security issues, migration risk, and missing tests. Use when reviewing a PR, git diff, or release critical change.
compatibility: Designed for Claude Code. Requires git and gh.
disable-model-invocation: true
allowed-tools: Bash(git diff *) Bash(gh pr diff *) Read Grep Glob
---
# Review PR
Read references/checklist.md before running any commands.
1. Collect the diff and changed files.
2. Flag correctness, security, and test coverage issues.
3. Return findings grouped by severity with file references.
4. Suggest the smallest safe fix first.