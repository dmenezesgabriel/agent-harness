---
name: find-nested-branches
description: Lists Python functions that use else or elif branches or nest decisions more than one level deep — flat-methods smells. Use when reviewing or refactoring Python control flow, when asked which functions to flatten with guard clauses or a dispatch table, or when locating arrow-shaped code before a refactor.
compatibility: Requires python3 (stdlib only). Python source only.
---

# Find nested branches

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_nested_branches.py <path> [...]
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `elses`, `elifs`, `depth`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. `--help` lists the same.

A finding is a smell, not a verdict. For each one, decide with `principle-flat-methods`: guard clauses and early returns first, extraction or a dispatch table for genuine branching.

**Gotchas:**
- `depth` counts nested decision nodes (if/for/while/match); `try`, `with`, and comprehensions are not counted.
- Guard-clause cascades (`if: return`, `if: return`) do not nest and are not flagged — unless a branch inside them does.
- Counting findings is not a flatness score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts`
