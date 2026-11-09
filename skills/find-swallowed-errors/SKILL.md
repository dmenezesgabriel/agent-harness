---
name: find-swallowed-errors
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin exception handlers that swallow their error — empty or pass-only except/catch blocks, handlers that only return a value, and promise .catch callbacks that discard the rejection. Use when debugging a failure whose evidence disappeared, when auditing where errors go to die, or before fixing a symptom that keeps moving.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find swallowed errors

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_swallowed_errors.py <path> [...]   # Python
uv run scripts/find_swallowed_errors.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `handler`, `body`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a hiding place, not a verdict. For each one, decide with [principle-fix-root-causes](../principle-fix-root-causes/SKILL.md): whether the swallowed error is the evidence a recurring bug needs, and whether the state it discards is legitimate or impossible.

**Gotchas:**
- `handler` is `except`, `catch`, or `.catch()`; `body` is `empty` (pass/ellipsis/docstring/bare block) or `return` (every statement returns, discarding the error into a value).
- A handler that logs, re-raises, or calls anything is a response and is not flagged — even a log-then-return.
- `.catch(() => fallback)` flags only value bodies; a callback that invokes a function counts as handling.
- Kotlin `return` inside `catch` is flagged like other languages; `runCatching` and `Result` capture are explicit containers, not handlers, and are not flagged.
- Scans skip hidden directories and generated trees (`node_modules`, `dist`, `build`, `target`, `out`, `vendor`, `coverage`, `__pycache__`); pass a file or that directory explicitly to scan it anyway.
- Counting findings is not an error-handling score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
