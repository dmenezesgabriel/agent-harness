---
name: explore-codebase
description: Deep exploration of an unfamiliar codebase. Use when onboarding to a new repo, auditing architecture, or mapping module dependencies.
---

# Explore Codebase

Spawn a **pi coding agent** (`pi`) in `tmux` interactively to not block the main session. With `tmux` you should be able to send keys to the agent and see its output in real-time. The agent must perform the following steps:

1. Walk the directory tree and summarise the top-level modules.
2. Identify the main entry points and their responsibilities.
3. Map the dependency graph between packages.
4. Return a structured summary to the main session — not the raw file list.
