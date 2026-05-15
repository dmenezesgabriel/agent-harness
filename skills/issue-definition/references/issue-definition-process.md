# Issue Definition Process

Use this sequence to turn a request into an implementation-ready issue.

1. **Name the issue precisely**
   - Use a title that describes the actual change or problem.

2. **State the request in observable terms**
   - Describe current behavior, requested behavior, or the gap.
   - Avoid solution-first wording unless the solution is already decided.

3. **Capture context**
   - Note who is affected, where it happens, and why it matters now.

4. **Set scope and non-goals**
   - Say what is included.
   - Say what is explicitly excluded.

5. **List requirements**
   - Add functional requirements.
   - Add non-functional requirements only when they materially matter.

6. **Cover use cases and edge cases**
   - Include the primary flow first.
   - Add failure modes, empty states, invalid input, migration concerns, or regression-sensitive paths when relevant.

7. **Identify dependencies, constraints, and risks**
   - Include upstream systems, contracts, rollout limits, assumptions, and blocking unknowns.

8. **Write acceptance criteria**
   - Use concrete outcomes that can later be checked.
   - Use Given/When/Then when it helps clarity.

9. **State validation expectations**
   - Describe what kinds of tests, checks, demos, or review points should exist during implementation.

10. **Add readiness and completion gates**
   - Definition of Ready: what must be true before implementation starts.
   - Definition of Done: what must be true before the issue is considered complete.

11. **Slice the work**
   - Break the issue into the smallest meaningful implementation steps.

12. **Surface unresolved gaps explicitly**
   - If key information is missing, record it under assumptions, open questions, or Definition of Ready.
   - Do not hide ambiguity behind vague wording.
