# Frontend Verification

Use this reference when the change affects UI, interaction, or user-facing behavior.

Confirm the smallest set that proves the change works.

## Check for
- acceptance criteria and user-visible behavior
- semantic UI output such as correct roles, labels, headings, and status text when relevant
- focus order, keyboard access, and interaction without a pointer when relevant
- accessible names, validation messages, and error states when relevant
- state transitions such as loading, empty, success, error, disabled, and invalid states
- critical user flows only when the change touches them

## Practical rules
- verify the changed path first, then nearby states most likely to regress
- prefer targeted component or behavior tests before broader flow coverage
- use integration checks when routing, async data, or cross-component state is involved
- include build or type checks when the change affects compilation, bundling, or generated UI artifacts
- do not turn ordinary UI validation into broad visual review unless the task requires it
