# Skills workflow benchmarks

First scaffold for real-world-ish benchmarks covering:
- `skills/issue-definition`
- `skills/implementation-workflow`
- `skills/change-validation`

This is the first practical slice, not the full benchmark system.

## Goals

Measure whether the skills improve real task outcomes over a paired baseline:
- `with_skill`
- `without_skill`

Initial emphasis:
- narrow deterministic checks where feasible
- realistic task specs
- explicit artifact contracts
- workspace/report conventions under `.workspaces/skills-workflow-benchmarks/`

## Layout

```text
benchmarks/skills-workflow/
├── README.md
├── fixtures/
│   └── invite_workflow_app/
├── scenarios/
├── schemas/
├── scripts/
└── tasks/
    └── <task-id>/
        ├── task.json
        ├── fixtures/
        ├── public-tests/
        ├── hidden-tests/
        └── rubrics/
```

Runtime outputs live outside `skills/`:

```text
.workspaces/skills-workflow-benchmarks/
└── iteration-1/
    ├── .trusted-assets/
    │   └── <task-id>/
    │       └── <configuration>/run-1/
    │           ├── test-manifest.json
    │           └── tests/
    └── <task-id>/
        ├── with_skill/run-1/
        │   ├── repo/
        │   ├── artifacts/
        │   ├── outputs/
        │   │   ├── submission.patch
        │   │   └── protected-paths.json
        │   ├── public-results/
        │   ├── hidden-results/
        │   ├── trusted-eval/
        │   │   ├── repo/
        │   │   ├── metadata.json
        │   │   ├── patch-application.json
        │   │   ├── public-results/
        │   │   └── hidden-results/
        │   ├── execution-metadata.json
        │   └── run-metadata.json
        └── without_skill/run-1/
```

## Current task set

1. `backend-duplicate-invite-bugfix`
2. `fullstack-invite-flow-vertical-slice`
3. `bundled-unrelated-request-splitting`
4. `validation-only-false-confidence`

These come from the planned first-priority set.

## Task contract

Each task definition includes:
- task id and category
- target skills
- fixture source
- user-facing prompt and repo context
- success criteria
- required output artifacts
- paired run config
- public and hidden checks

See `schemas/` for the initial artifact and task shapes.

## Artifact conventions

Expected benchmark-produced artifacts:
- `artifacts/issue.json`
- `artifacts/implementation-report.json`
- `artifacts/validation-report.json`
- `run-metadata.json`
- `public-results/results.json`
- `hidden-results/results.json`

Initial schemas exist for:
- issue artifact
- implementation report
- validation report
- run result metadata

Task prompts now repeat the artifact contract in benchmark-facing language:
- exact artifact file paths
- reminder that missing artifacts fail the run even if code/tests pass
- a prominent immutable-assets warning that benchmark-owned tests/check assets must not be edited
- schema-backed required keys and enum constraints
- concise JSON examples for each required artifact in the task definition

Artifact files should always be plain JSON objects matching their schema. Do not write Markdown, prose-only notes, or fenced JSON into those files.

Current schema-required top-level fields:
- `issue.json`: `summary`, `problem`, `scope`, `acceptance_criteria`, `non_goals`, `validation_expectations`
- `implementation-report.json`: `summary`, `files_changed`, `route`, `tests_run`, `risks`
- `validation-report.json`: `status`, `checks_run`, `findings`, `recommendation`

This slice does **not** implement judge-based grading or a hardened sandbox. It now has two validation paths:
- the preferred trusted two-workspace patch-eval path
- the older restore-before-check fallback path for legacy/local compatibility

It also enforces required artifact schemas.

## Primary harness flow

### 1. Validate task definitions

```bash
python benchmarks/skills-workflow/scripts/validate_task_defs.py
```

### 2. Run a paired benchmark task through Pi

```bash
python benchmarks/skills-workflow/scripts/run_task.py \
  benchmarks/skills-workflow/tasks/backend-duplicate-invite-bugfix \
  --reinitialize
```

This now initializes `with_skill/run-1` and `without_skill/run-1`, launches Pi for each prepared workspace, then finalizes both runs.

Optional Pi flags can be forwarded:

```bash
python benchmarks/skills-workflow/scripts/run_task.py \
  benchmarks/skills-workflow/tasks/backend-duplicate-invite-bugfix \
  --reinitialize \
  --provider google \
  --model gemini-2.5-pro
```

### 3. Execution contract

For each run, the harness creates `agent-prompt.md` plus `run-metadata.json` with an explicit contract:
- prompt is passed to Pi as `@<run-dir>/agent-prompt.md`
- Pi executes inside `<run-dir>/repo`
- `with_skill` loads only the task's declared `skill_targets` via explicit `--skill <abs-path>` flags
- `without_skill` runs with `--no-skills`
- required benchmark artifacts must be written under `<run-dir>/artifacts/`
- the prompt now includes a high-priority immutable-assets section forbidding edits to benchmark-owned tests/check assets
- `run-metadata.json` now also records `completion_contract.immutable_paths` as a lightweight preflight signal
- Pi stdout/stderr are captured under `<run-dir>/outputs/`
- session files are stored under `<run-dir>/pi-session/` when available
- completion is detected automatically by Pi process exit; the harness synthesizes `outputs/completion.json` if the agent did not write one itself

### 4. Persisted outputs

Each run persists:
- `execution-metadata.json`
- `outputs/pi-stdout.txt`
- `outputs/pi-stderr.txt`
- `outputs/completion.json`
- `outputs/submission.patch`
- `outputs/submission-diff.json`
- `outputs/protected-paths.json`
- trusted asset references in `run-metadata.json` / integrity reports
- `artifact-summary.json`
- `artifact-schema-validation.json`
- `public-results/asset-integrity.json`
- `public-results/results.json`
- `hidden-results/asset-integrity.json`
- `hidden-results/results.json`
- `trusted-eval/metadata.json`
- `trusted-eval/patch-application.json`
- `trusted-eval/public-results/results.json`
- `trusted-eval/hidden-results/results.json`
- `run-summary.json`

Task-level paired status is written to `benchmark-summary.json`.

### 5. Manual fallback mode

Automatic execution is now the primary path, but the old file contract still exists as fallback:

```bash
python benchmarks/skills-workflow/scripts/run_task.py \
  benchmarks/skills-workflow/tasks/backend-duplicate-invite-bugfix \
  --manual-only
```

In manual mode:
- make repo changes inside `repo/`
- write artifacts under `artifacts/`
- create `outputs/completion.json`
- rerun the harness with `--manual-only` to execute checks/finalization only

### 6. Run visible/hidden checks directly if needed

```bash
python benchmarks/skills-workflow/scripts/run_checks.py \
  benchmarks/skills-workflow/tasks/backend-duplicate-invite-bugfix \
  .workspaces/skills-workflow-benchmarks/iteration-1/backend-duplicate-invite-bugfix/with_skill/run-1 \
  --phase public
```

### 7. Summarize one task workspace

```bash
python benchmarks/skills-workflow/scripts/summarize_workspace.py \
  .workspaces/skills-workflow-benchmarks/iteration-1/backend-duplicate-invite-bugfix
```

## Fixture repo

`fixtures/invite_workflow_app/` is the tiny canonical repo for this first slice.

It intentionally contains:
- a backend duplicate-invite bug
- a fullstack-ish submit/retry bug
- deterministic `unittest` suites split into public and hidden checks

Why tiny?
- faster to understand
- deterministic to validate
- enough to make next benchmark steps obvious

## What is implemented vs stubbed

Implemented now:
- benchmark directory scaffold
- protocol/readme
- task/spec schemas
- paired workspace initialization
- trusted two-workspace patch evaluation for all current tasks
- hidden tests removed from the agent workspace for tasks that actually have hidden checks
- task-level paired run entrypoint
- real Pi CLI execution for paired runs
- explicit prompt/skill/artifact/completion contract per run
- automatic completion synthesis with manual fallback
- patch capture from the agent workspace via git diff
- protected-path filtering before trusted patch application
- trusted public/hidden check runner in the separate evaluator workspace
- required artifact schema validation during finalization
- per-run artifact and result summaries
- task-level paired benchmark summary
- 4 concrete task definitions
- tiny fixture repo with deterministic backend/fullstack tests
- scenario and rubric placeholders

Still stubbed or partial:
- transcript/session capture depends on Pi session output availability
- no hardened sandbox beyond local workspace separation, trusted copies, patch filtering, and patch application
- no benchmark-wide multi-task aggregation yet
- routing/artifact grading for split-only tasks is metadata-first, not judge-complete

## Integrity and validation guarantees

The local harness now protects benchmark-owned test files in a more credible way:
- all current tasks get a separate `run-1/trusted-eval/repo/` evaluator workspace alongside the agent `run-1/repo/` workspace
- tasks with hidden checks remove those hidden tests from the agent workspace; they exist only in the trusted evaluator copy
- the agent submission is captured as `outputs/submission.patch`
- patch paths are inspected and persisted to `outputs/protected-paths.json`
- patches touching protected benchmark-owned paths such as `tests/**` are rejected before trusted evaluation
- the trusted evaluator now tries real `git apply --check` / `git apply --binary` patch application first
- if strict patch application fails, the harness records that and falls back to an explicit file-projection sync for touched paths
- trusted evaluator metadata and patch-application status are persisted under `trusted-eval/`
- the older restore-before-check path still exists, but it is now the fallback path rather than the main model

Required artifacts are also enforced more strictly:
- missing artifacts still fail the run
- schema-backed artifacts must parse as JSON and satisfy their declared schema
- schema validation results are persisted to `artifact-schema-validation.json`
- a run is not cleanly successful when required artifacts fail schema validation

Remaining limitations:
- this is still local harness integrity, not a full sandbox; a determined local actor with the same OS user could override file permissions or walk outside the repo if allowed by the execution environment
- the main improvement is now workspace separation plus patch-based trusted evaluation for all current tasks
- the patch filter is path-based, not semantic; it rejects benchmark-owned locations but does not yet do deeper policy analysis
- schema validation currently supports the subset used by the benchmark schemas in this repo (`type`, `required`, `properties`, `items`, `enum`)

## Recommended next implementation steps

1. Add benchmark aggregation compatible with the `skill-builder` report shape.
2. Improve result scoring for non-code-routing tasks.
3. Add stricter deterministic assertions for artifact-only tasks like `bundled-unrelated-request-splitting`.
4. Add a second fixture repo after this scaffold stabilizes.
