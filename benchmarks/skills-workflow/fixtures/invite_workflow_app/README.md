# Invite workflow fixture

Tiny Python fixture repo for the first benchmark slice. It intentionally contains:
- a backend duplicate-invite bug in `app/invites.py`
- a fullstack-ish state bug in `app/invite_flow.py`
- deterministic public and hidden `unittest` suites

The fixture is small on purpose so the benchmark scaffold stays understandable.
