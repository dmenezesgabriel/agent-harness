# Check Selection and Risk Mapping

Use this as the canonical risk-to-check mapping when choosing the smallest sufficient validation set.

Prefer the smallest relevant set first. Expand only when scope, risk, or failures justify it.

## Common mappings

### Small isolated logic change
- targeted unit or regression tests
- type check when the ecosystem uses it
- lint only if the touched area commonly fails lint or CI requires it

### Frontend change
- targeted component or behavior tests
- accessibility-focused checks when labels, focus, keyboard behavior, semantics, or errors changed
- integration checks if the UI depends on routing, async data flow, or cross-component state
- build or type checks if compilation or bundling is affected

### Backend change
- targeted unit tests for the rule or invariant
- integration or handler/service tests for the affected seam
- contract or schema checks for request, response, or message boundaries
- build or type checks when relevant

### Dependency update
- targeted tests for affected areas
- build or package checks
- dependency audit for the ecosystem when relevant:
  - `pnpm audit` or `npm audit`
  - `pip-audit`
- expand only if release notes, advisories, or failures indicate risk

### Auth, authorization, trust-boundary, file-handling, or sensitive-data change
- targeted tests for allowed, denied, and error paths
- integration checks at the trust boundary
- security scan when available and justified, for example:
  - `semgrep --config auto`
  - ecosystem dependency audit
- use `security-vulnerability-audit` when the change or request clearly justifies deeper review

### Fullstack or seam/contract change
- targeted frontend and backend checks at their owning boundaries
- integration or contract checks for the seam
- type/build checks when either side depends on them
- expand to critical-flow verification only for the changed path

### Build, config, CI, migration, or widely shared library change
- targeted tests plus adjacent integration checks
- lint, type, and build checks
- smoke path for the most critical affected flow

## Selection reminders
- choose checks by affected surface and risk, not habit
- record why the selected set is sufficient
- note what you intentionally skipped and why
- do not run the entire check suite when a smaller set can establish confidence
- do not skip a necessary higher-level check when the change crosses that boundary

## One-off commands vs scripts

Use one-off commands when the project already exposes the needed tool and the invocation is short.

Create or use a script only when:
- the same multi-step validation flow is repeated often
- the command syntax is fragile or hard to remember
- the script can standardize output and failure modes
- the script meaningfully reduces repeated agent work
