---
name: find-feature-envy
description: Lists Python functions that read three or more distinct attributes of one foreign parameter — a tell-don't-ask smell where the function does the value's job. Use when reviewing Python code for misplaced logic, when asked which functions keep pulling fields out of one object instead of asking it for the result, or when hunting anemic-model drift before a refactor.
compatibility: Requires python3 (stdlib only). Python source only.
---

# Find feature envy

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_feature_envy.py <path> [...]
```

Output is one JSON object per finding on stdout (`path`, `line`, `name`, `target`, `attrs`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. `--help` lists the same.

A finding is a smell, not a verdict. For each one, decide with `principle-tell-dont-ask`: move the computation next to `target`'s data, or keep it when the rule belongs to the caller.

**Gotchas:**
- Only attributes read directly on a function parameter count; nested chains (`order.customer.x`) count their first hop — see `find-train-wrecks` for those.
- Serializers, mappers, and constructors legitimately touch many fields of one value; that is their job, not envy.
- Dict/subscript access is not counted (it is a traversal, not an attribute read).
- Counting findings is not a cohesion score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts`
