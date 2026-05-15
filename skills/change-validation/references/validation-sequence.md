# Validation Sequence

Use this sequence for post-implementation validation.

1. Confirm scope
   - restate the exact change being validated
   - confirm acceptance criteria, Definition of Done, constraints, and explicit non-goals
   - identify affected surfaces such as frontend, backend, fullstack seams, API, data, config, or tests

2. Choose the smallest sufficient validation set
   - start with the checks most likely to catch regressions in the affected area
   - include higher-level checks only when the change crosses that boundary or risk justifies it
   - note what you are intentionally not running and why

3. Run the checks
   - execute the selected tests, type/build checks, or manual verification steps
   - keep the run focused on the approved scope

4. Inspect failures
   - decide whether each failure is change-caused, pre-existing, flaky, or expected from the change
   - do not assume every failing check is part of the current work

5. Fix in-scope regressions
   - correct failures introduced or exposed by the change when they are within approved scope
   - add or adjust regression coverage only when needed to protect the changed behavior

6. Re-run the relevant checks
   - rerun the smallest sufficient set to confirm the fix
   - expand only if failures or risk show the original set was insufficient

7. Summarize readiness
   - record what was validated
   - state pass, fail, or blocked status
   - note residual risk, pre-existing issues, or intentionally unvalidated areas
   - conclude whether the change is ready to merge
