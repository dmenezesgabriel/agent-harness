# Surface and Work-Type Examples

Load this reference when classification is unclear or when the issue needs sharper fork-specific prompts.

## Step 1: Classify the surface

### Frontend
Use when the main change is in UI behavior.

Make these explicit:
- visible states: loading, empty, success, error, disabled, invalid
- key user interactions
- accessibility expectations
- responsive or layout constraints

Example:
- `On the billing page, the retry-payment button stays disabled until the card form is valid and shows the API error inline when the retry fails.`

### Backend
Use when the main change is in rules, contracts, or data flow.

Make these explicit:
- domain rules and invariants
- API, event, or job contracts
- persistence impact
- failure handling

Example:
- `A second identical webhook event is ignored and returns 200 without creating a duplicate payment record.`

### Fullstack
Use when the user-visible flow crosses the frontend/backend seam.

Make these explicit:
- end-to-end flow
- boundary between frontend and backend
- contract crossing the seam
- sequencing if one side must land first

Example:
- `Users can request an invoice from the order screen, the API queues PDF generation, and the UI updates from pending to ready when the document is available.`

## Step 2: Classify the work type

### Feature
Use when the issue adds net-new behavior.

Make these explicit:
- user or operator value
- new behavior
- affected workflow
- rollout or compatibility constraints

Example:
- `Users can duplicate an existing report from the report details page.`

### Bugfix
Use when the issue restores expected behavior.

Make these explicit:
- current behavior
- expected behavior
- reproduction conditions
- impact and regression-sensitive paths

Example:
- `After session timeout, a user who submits valid credentials stays stuck on the loading state instead of reaching the dashboard.`

### Refactor
Use when the issue improves structure without changing intended behavior.

Make these explicit:
- behavior that must not change
- design problem being improved
- migration or compatibility constraints
- safety boundaries for incremental change

Example:
- `Extract notification delivery logic so email and in-app channels can change independently without changing user-visible behavior.`

### Improvement
Use when the issue improves an existing workflow or operational characteristic.

Make these explicit:
- what gets better
- how the improvement is observed
- what stays unchanged

Example:
- `Reduce report generation time from 12s to under 5s for the standard dataset without changing report contents.`

### Research-backed change
Use when the issue implements a change justified by evidence from research, support trends, analytics, or a prior investigation.

Make these explicit:
- source of the finding
- key insight or recommendation
- resulting behavior change
- expected effect

Example:
- `Based on support-call review, replace the hidden password reset link with a primary action on the sign-in screen to reduce reset-related drop-offs.`
