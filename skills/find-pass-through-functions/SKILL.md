---
name: find-pass-through-functions
description: Lists Python, TypeScript, JavaScript, Java, and Kotlin functions whose body only forwards their own parameters unchanged to another call, a shallow-module smell. Use when reviewing or refactoring wrappers, service or adapter layers, or when asked whether a class or function adds anything over what it calls.
compatibility: Python files need only python3 (stdlib). TypeScript/JavaScript/Java/Kotlin need uv, which installs the PEP 723 dependency declared in the script (tree-sitter-language-pack).
---

# Find pass-through functions

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_pass_through.py <path> [...]   # Python
uv run scripts/find_pass_through.py <path> [...]       # + TS/JS/Java/Kotlin (installs deps)
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `callee`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. Files that fail to parse are skipped with a warning on stderr; exit 2 when no file could be parsed. `--help` lists the same. Supported suffixes: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.kts`.

A finding is a smell, not a verdict. For each one, decide with `principle-modules-should-be-deep`: remove the layer, or keep it only if it adds policy, adaptation, or a distinct abstraction.

**Gotchas:**
- Not reported on purpose: decorated/annotated functions, `super()` calls, zero-argument functions, and any body that transforms, reorders, or adds an argument.
- No finding does not mean the module is deep. It only means no exact forwarding was found.
- Counting findings is not a depth score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts` (Python only; language tests skip) and `uv run --with tree-sitter-language-pack python -I -m unittest discover -s scripts` (all languages).
