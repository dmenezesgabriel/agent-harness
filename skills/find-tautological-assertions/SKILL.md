---
name: find-tautological-assertions
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin assertions that cannot fail — an expression compared to itself (assertEquals(x, x), expect(x).toBe(x), assert x == x) or a constant-true assertion (assertTrue(true), assert True). Use when a test suite passes while the feature is broken, when auditing tests for hollow coverage, or when reviewing generated or refactored tests.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find tautological assertions

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_tautological_assertions.py <path> [...]   # Python
uv run scripts/find_tautological_assertions.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `assertion`, `kind`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a smell, not a verdict. For each one, decide with [principle-test-behavior-not-implementation](../principle-test-behavior-not-implementation/SKILL.md): a test that cannot fail proves nothing — rewrite it against observable behavior or delete it.

**Gotchas:**
- `kind` is `same-operands` (identical expressions on both sides of an equality assertion) or `always-true` (a literal constant asserted as truthy — `assertTrue(true)`, `assert True`, `expect(true).toBeTruthy()`).
- Operands compare after whitespace and outer parentheses are stripped; `assertEqual(x, x)` and `assertEqual((x), (x))` are the same tautology.
- Asserts that cannot pass (`assert x != x`, `assertFalse(true)`) are dead differently and are not flagged.
- `assertFalse(false)` is flagged as `always-true` — the assertion holds whatever the code does.
- Scans skip hidden directories and generated trees (`node_modules`, `dist`, `build`, `target`, `out`, `vendor`, `coverage`, `__pycache__`); pass a file or that directory explicitly to scan it anyway.
- Counting findings is not a test-quality score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
