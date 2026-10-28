---
name: find-train-wrecks
description: Lists Python expressions that reach through three or more links — attribute, subscript, or call chains like order.customer.address.city or cfg["a"]["b"]["c"] — Law of Demeter smells. Use when reviewing Python code for structural coupling, when asked where callers traverse other objects' internals, or when locating chain expressions before a refactor.
compatibility: Requires python3 (stdlib only). Python source only.
---

# Find train wrecks

Run from this skill's root, on a file or directory:

```bash
python3 -I scripts/find_train_wrecks.py <path> [...]
```

Output is one JSON object per finding on stdout (`path`, `line`, `expression`, `hops`); errors go to stderr. Exit 0 none, 1 found, 2 bad input. `--help` lists the same.

A finding is a smell, not a verdict. For each one, decide with `principle-law-of-demeter`: move the outcome onto the nearest collaborator, or leave it when the chain is a fluent interface.

**Gotchas:**
- Static analysis cannot tell a traversal from a fluent API — `query.where(...).order_by(...)` flags just like `a.b.c.d`. Fluent findings are false positives; judge each one.
- The first hop on `self`/`cls` is free — it is the code's own member, not a stranger.
- Only the maximal chain is reported, so a finding's prefixes are not listed separately.
- Counting findings is not a coupling score; do not optimize the count.

Tests: `python3 -I -m unittest discover -s scripts`
