---
name: find-train-wrecks
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin expressions that reach through three or more links — attribute, subscript, or call chains like order.customer.address.city or cfg["a"]["b"]["c"] — Law of Demeter smells. Use when reviewing code for structural coupling, when asked where callers traverse other objects' internals, or when locating chain expressions before a refactor.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find train wrecks

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_train_wrecks.py <path> [...]   # Python
uv run scripts/find_train_wrecks.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `expression`, `hops`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a smell, not a verdict. For each one, decide with [principle-law-of-demeter](../principle-law-of-demeter/SKILL.md): move the outcome onto the nearest collaborator, or leave it when the chain is a fluent interface.

**Gotchas:**
- Static analysis cannot tell a traversal from a fluent API — `query.where(...).order_by(...)` flags just like `a.b.c.d`. Fluent findings are false positives; judge each one.
- The first hop on `self`/`cls`/`this` is free — it is the code's own member, not a stranger.
- Only the maximal chain is reported, so a finding's prefixes are not listed separately.
- Scans skip hidden directories and generated trees (`node_modules`, `dist`, `build`, `target`, `out`, `vendor`, `coverage`, `__pycache__`); pass a file or that directory explicitly to scan it anyway.
- Counting findings is not a coupling score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
