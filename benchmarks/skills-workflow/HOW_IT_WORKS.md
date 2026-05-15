# Skills Workflow Benchmark Harness

## Purpose
This benchmark harness compares `with_skill` vs `without_skill` runs on realistic agent tasks.

It measures:
- task correctness
- artifact correctness
- benchmark integrity
- compactness / efficiency
- relative skill value

## What it benchmarks
Current workflow skills:
- `skills/issue-definition`
- `skills/implementation-workflow`
- `skills/change-validation`

Task definitions live in:
- `benchmarks/skills-workflow/tasks/`

## Main design
The harness uses two workspaces.

### 1. Agent workspace
This is the repo copy the agent edits.

The agent can:
- read task instructions
- read visible repo files
- edit allowed files
- write required artifacts

The agent should not edit benchmark-owned assets.

### 2. Trusted evaluator workspace
This is a fresh trusted repo copy used only for grading.

It contains:
- trusted public tests
- hidden tests
- trusted benchmark assets

The agent does not grade inside its own edited repo for covered tasks.

## Why this matters
This prevents a fake pass by editing tests or benchmark-owned files.

The harness evaluates the submitted change in a clean trusted workspace.

## Submission model
For trusted-eval tasks, the harness captures the agent output as a patch/diff.

Then it:
1. filters protected paths
2. creates a fresh trusted evaluator repo
3. applies the submitted patch
4. runs public checks
5. runs hidden checks
6. validates required artifacts
7. writes summaries

## Protected paths
Protected paths are benchmark-owned files that must not be edited.

Typical protected paths include:
- `tests/test_public_*.py`
- `tests/test_hidden_*.py`
- benchmark result directories
- benchmark-managed validation assets

If protected paths are modified, the run fails integrity.

## Artifact validation
Many tasks require JSON artifacts.

Examples:
- issue artifacts
- implementation reports
- validation reports

The harness checks:
- file exists
- valid JSON
- schema-valid structure

A run can fail even if tests pass when required artifacts are missing or invalid.

## Task types
There are two broad categories.

### Code-change tasks
These require repo changes.

Examples:
- `backend-duplicate-invite-bugfix`
- `fullstack-invite-flow-vertical-slice`
- `validation-only-false-confidence`

These usually use trusted patch evaluation.

### Artifact / routing tasks
These mostly evaluate structured reasoning artifacts.

Example:
- `bundled-unrelated-request-splitting`

These focus on:
- decomposition quality
- routing correctness
- artifact quality
- compactness

## Important result files
Per task:
- `benchmark-summary.json`

Per run:
- `run-summary.json`
- `run-metadata.json`
- `execution-metadata.json`
- `artifact-summary.json`
- `artifact-schema-validation.json`
- `public-results/results.json`
- `hidden-results/results.json`

For trusted-eval runs:
- `outputs/submission.patch`
- `outputs/protected-paths.json`
- `trusted-eval/metadata.json`
- `trusted-eval/patch-application.json`

## How to run one task
Validate task definitions:

```bash
python3 benchmarks/skills-workflow/scripts/validate_task_defs.py
```

Run one task:

```bash
python3 benchmarks/skills-workflow/scripts/run_task.py benchmarks/skills-workflow/tasks/<task-id> --reinitialize
```

Example:

```bash
python3 benchmarks/skills-workflow/scripts/run_task.py benchmarks/skills-workflow/tasks/backend-duplicate-invite-bugfix --reinitialize
```

## Where outputs go
Outputs are written under:

- `.workspaces/skills-workflow-benchmarks/<iteration>/<task-id>/`

Example:

- `.workspaces/skills-workflow-benchmarks/iteration-1/backend-duplicate-invite-bugfix/`

## How `with_skill` vs `without_skill` works
Both runs use:
- same task
- same fixture
- same benchmark checks
- same workspace pattern

Difference:
- `with_skill` injects the target skill
- `without_skill` disables skills

This isolates the effect of the skill as much as practical.

## How to read results
Start with:
1. overall run status
2. public result
3. hidden result
4. artifact schema result
5. integrity result
6. efficiency metrics

### Good result
A strong result means:
- `with_skill` passes more often
- or passes with smaller / cleaner artifacts
- or reaches similar correctness with lower cost

### Bad result
A weak result means:
- both pass equally with no measurable gain
- `with_skill` is more verbose with no quality gain
- `with_skill` fails while baseline passes

### Mixed result
A mixed result means:
- skill improves routing/triggering but not output quality
- skill improves correctness but increases verbosity/cost

## Efficiency signals
Common efficiency signals:
- duration
- artifact size
- `total_chars` in validator output
- output file sizes

Use them only after correctness is acceptable.

Correctness first. Efficiency second.

## Current limitations
This is a strong local harness, not a hardened sandbox.

Current limits:
- trust boundary is local, not adversarial-grade isolation
- some tasks are more discriminative than others
- benchmark quality still depends on task/rubric design
- repeated-run variance is not yet the default everywhere

## Recommended workflow
1. change or add a task
2. validate task definitions
3. run paired `with_skill` / `without_skill`
4. inspect summaries
5. compare correctness first
6. compare compactness / cost second
7. improve either the skill or the benchmark based on evidence

## When to trust a result
Trust a result more when:
- public and hidden checks agree
- artifact validation passes
- integrity is clean
- repeated runs show similar outcomes
- the task clearly separates skill vs baseline

Do not over-interpret one noisy task.

Use several tasks and compare patterns.