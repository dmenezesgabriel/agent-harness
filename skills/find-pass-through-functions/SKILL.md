---
name: find-pass-through-functions
description: Lists Python functions whose body only forwards their own parameters unchanged to another call, a shallow-module smell. Use when reviewing or refactoring Python wrappers, service or adapter layers, or when asked whether a class or function adds anything over what it calls.
compatibility: Requires python3 (stdlib only). Python source only.
---

# Find pass-through functions

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_pass_through.py <path> [...]
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `callee`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. `--help` lists the same.

A finding is a smell, not a verdict. For each one, decide with `principle-modules-should-be-deep`: remove the layer, or keep it only if it adds policy, adaptation, or a distinct abstraction.

**Gotchas:**
- Not reported on purpose: decorated functions, `super()` calls, zero-argument functions, and any body that transforms, reorders, or adds an argument.
- No finding does not mean the module is deep. It only means no exact forwarding was found.
- Counting findings is not a depth score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts`
