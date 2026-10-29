---
name: find-nested-branches
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin functions that use else or elif branches or nest decisions more than one level deep — flat-methods smells. Use when reviewing or refactoring control flow, when asked which functions to flatten with guard clauses or a dispatch table, or when locating arrow-shaped code before a refactor.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find nested branches

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_nested_branches.py <path> [...]   # Python
uv run scripts/find_nested_branches.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `elses`, `elifs`, `depth`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a smell, not a verdict. For each one, decide with `principle-flat-methods`: guard clauses and early returns first, extraction or a dispatch table for genuine branching.

**Gotchas:**
- `depth` counts nested decision nodes (if/for/while/match, switch, `when`); `try`, `with`, and comprehensions are not counted.
- Guard-clause cascades (`if: return`, `if: return`) do not nest and are not flagged — unless a branch inside them does.
- Kotlin `if` in value position (`val x = if (a) 1 else 2`) is a ternary, not a branch, and is not flagged.
- Scans skip hidden directories and generated trees (`node_modules`, `dist`, `build`, `target`, `out`, `vendor`, `coverage`, `__pycache__`); pass a file or that directory explicitly to scan it anyway.
- Counting findings is not a flatness score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
