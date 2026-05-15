### Implementation Workflow: <precise change name>

Issue taxonomy:
- Surface: Frontend | Backend | Fullstack
- Work type: Feature | Bugfix | Refactor | Improvement | Research-backed change

Routing decision:
<chosen workflow and why>

Behavior to implement or protect:
<required behavior, invariant, contract, or regression path>

Owning boundary:
<domain object / use case / API contract / component / screen / module>

First protection:
<failing test / repro / regression test / characterization test / component behavior scenario>

Smallest change:
<minimum implementation step>

Local proof run during implementation:
- <targeted check and why it proves the changed behavior>

Remaining risk:
<any remaining coupling / invariant / contract / migration / UI / regression risk>

Handoff status:
Ready for final change-validation | Blocked | Needs more implementation

Recommended final validation scope:
- <acceptance criteria or DoD item to confirm>
- <broader check that should happen after implementation>
