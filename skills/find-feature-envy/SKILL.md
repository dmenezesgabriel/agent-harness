---
name: find-feature-envy
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin functions that read three or more distinct attributes of one foreign parameter — a tell-don't-ask smell where the function does the value's job. Use when reviewing code for misplaced logic, when asked which functions keep pulling fields out of one object instead of asking it for the result, or when hunting anemic-model drift before a refactor.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find feature envy

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_feature_envy.py <path> [...]   # Python
uv run scripts/find_feature_envy.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `target`, `attrs`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a smell, not a verdict. For each one, decide with `principle-tell-dont-ask`: move the computation next to `target`'s data, or keep it when the rule belongs to the caller.

**Gotchas:**
- Only attributes read directly on a function parameter count; nested chains (`order.customer.x`) count their first hop — see `find-train-wrecks` for those.
- Method calls on the parameter (`u.get_a()`) count as attribute reads, matching the Python detector.
- Serializers, mappers, and constructors legitimately touch many fields of one value; that is their job, not envy.
- Dict/subscript access is not counted (it is a traversal, not an attribute read).
- Counting findings is not a cohesion score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
