---
id: "041"
created: 2026-05-24
updated: 2026-05-24
status: active
---

# Task: Create review-it benchmark task suite

## Priority

P2 — plan-it and implement-it benchmarks are now the measurement priority (Tasks 039–040). review-it has no tasks at all; this task closes that gap after the higher-priority fixes are in.

## Dependencies

- Depends on Task 040: `"llm_judge"` must be registered before review-it tasks can include it in their `evaluators` list.
- No ADR dependency; workspace seeding follows the existing `Task` extension pattern.

## Assignability

**HITL** — The gold-standard code and issue content embedded in `seed_files` must be reviewed by a human before committing. Seeded content that is ambiguous or incorrect will produce misleading benchmark signal, and correctness cannot be verified by static analysis alone.

## Context

`benchmarks/tasks/review-it/` does not exist. Running the benchmark for `review-it` exits immediately with "No tasks found." The runner and pi adapter are otherwise skill-agnostic; the missing pieces are:

1. **Workspace seeding**: review-it reads from `tasks/issues/<NNN>.md` and from code files on disk. Benchmark tasks must pre-populate the workspace with an issue file and code before pi runs. The `Task` model has no `seed_files` field today.

2. **Output collection**: the pi adapter's `_OUTPUT_GLOBS` and `_OUTPUT_DIRS` do not include `tasks/reviews/`, which is where the skill writes its report. The adapter will collect an empty `raw_output` and the code evaluator and behave evaluator will find no output.

3. **Behave feature file**: `benchmarks/features/review-it.feature` does not exist.

4. **Task JSON corpus**: three tasks are sufficient for a meaningful signal at low token cost:
   - `001-correct-impl.json` — correct implementation; expect "Pass" verdict, zero Blocking findings.
   - `002-missing-acceptance-criterion.json` — implementation that skips one AC; expect at least one Blocking finding.
   - `003-missing-test-coverage.json` — implementation with an untested requirement; expect Non-blocking findings on test coverage.

```
benchmarks/
├── features/review-it.feature          ← new
├── tasks/review-it/
│   ├── 001-correct-impl.json           ← new
│   ├── 002-missing-acceptance-criterion.json  ← new
│   └── 003-missing-test-coverage.json  ← new
harness/
├── models.py                           ← add seed_files field to Task
└── adapters/pi_agent.py                ← write seed_files + add tasks/reviews glob
```

## Use Cases

- **Feature**: review-it benchmarking
- **Scenario**: Harness measures review quality on a seeded workspace
- **Given** a review-it task with a seeded issue file and code file
- **When** pi runs the review-it skill
- **Then** a review report appears in `tasks/reviews/` and is captured in the workspace snapshot

- **Scenario**: Behave checks review structure
- **Given** the agent wrote `tasks/reviews/001-correct-impl-review.md`
- **When** the behave evaluator runs
- **Then** all structural scenarios in `review-it.feature` pass or fail based on actual content

## Definition of Ready

- Task 040 is complete and `"llm_judge"` is registered.
- `harness/models.py` `Task` dataclass is inspectable to confirm `seed_files` field does not already exist.
- The review-it skill output template (`skills/review-it/assets/review-report-template.md`) confirms the required sections: `Overall Verdict`, `Findings`, `AC Evaluation`, `Test Coverage Evaluation`.

## Functional Requirements

- `FR-001`: `Task` dataclass in `harness/models.py` must gain a `seed_files: dict[str, str]` field (default empty dict) mapping workspace-relative paths to file content.
- `FR-002`: `Task.from_dict()` must deserialize `seed_files` from the task JSON when present.
- `FR-003`: `PiAgentAdapter.run()` must write each `seed_files` entry into the workspace directory before invoking pi, creating parent directories as needed.
- `FR-004`: `_OUTPUT_DIRS` in `pi_agent.py` must include `"tasks/reviews"` so the workspace directory exists before pi runs.
- `FR-005`: `_OUTPUT_GLOBS` in `pi_agent.py` must include `"tasks/reviews/**/*.md"` so review reports are collected into `raw_output` and the workspace snapshot.
- `FR-006`: `benchmarks/features/review-it.feature` must assert: the `tasks/reviews` directory exists; at least one `.md` file exists in it; every review file contains a non-empty `Overall Verdict` section; every review file contains a non-empty `Findings` section; every review file contains a non-empty `AC Evaluation` section.
- `FR-007`: Three task JSON files must exist in `benchmarks/tasks/review-it/` with `"evaluators": ["behave", "llm_judge"]` and `seed_files` pre-populating a plausible issue file and a matching Python implementation.

## Non-Functional Requirements

- `NFR-001`: Seed file writes must happen before `pi` is invoked and after `workspace_manager.init_workspace()` returns, so the workspace snapshot baseline (`before`) excludes them.
- `NFR-002`: Each review-it task's seeded code must be short (≤50 lines of Python) to keep prompt size minimal and latency under 120 s.
- `NFR-003`: The behave feature file must reuse step definitions from `features/steps/common_steps.py` wherever the required assertions already exist there.

## Observability Requirements

- `OBS-001`: Not applicable — harness has no production telemetry.

## Acceptance Criteria

- `AC-001`: **Given** `uv run python run.py --skill review-it --platform pi-agent`, **When** executed, **Then** the runner processes 3 tasks without a "No tasks found" error.
- `AC-002`: **Given** the 3 review-it tasks run, **When** results are aggregated, **Then** `behave_pass_rate` is non-default (behave ran) and `judge_score` is non-zero (llm_judge ran).
- `AC-003`: **Given** a task with `seed_files: {"tasks/issues/001-example.md": "<content>"}`, **When** `PiAgentAdapter.run()` executes, **Then** the file exists in the workspace before pi is invoked.
- `AC-004`: **Given** the workspace snapshot after a review-it run, **When** inspected, **Then** at least one file matching `tasks/reviews/*.md` is present.
- `AC-005`: **Given** the behave feature runs on a workspace with a well-formed review report, **When** all scenarios execute, **Then** `Overall Verdict`, `Findings`, and `AC Evaluation` scenarios pass.

## Required Tests

### Unit Tests

- `UT-001`: Construct a `Task` with `seed_files={"tasks/issues/001.md": "# Task\ncontent"}`. Assert `task.seed_files["tasks/issues/001.md"] == "# Task\ncontent"`. Covers `FR-001`, `FR-002`.
- `UT-002`: Mock workspace path. Call `PiAgentAdapter.run()` with a task that has one `seed_files` entry. Assert the file was written at the correct path before the `subprocess.run` call. Covers `FR-003`.

### Integration Tests

- `IT-001`: **Scenario**: review-it benchmark runs end-to-end  
  **Given** `benchmarks/tasks/review-it/001-correct-impl.json` exists with `seed_files`  
  **When** `uv run python run.py --skill review-it --platform pi-agent --task-ids review-it-001 --dry-run` is executed  
  **Then** the process exits 0 and prints a results table with `behave_pass_rate` set  
  Covers `FR-003`, `FR-005`, `AC-001`, `AC-002`.

### Smoke Tests

Not applicable — covered by integration test above.

### End-to-End Tests

Not applicable — integration test is sufficient.

### Regression Tests

Not applicable — no previous defect.

### Performance Tests

Not applicable — seed file writes are O(n) over small files; no latency constraint beyond NFR-002.

### Security Tests

Not applicable — seed files are corpus-controlled; no user-supplied content.

### Usability Tests

Not applicable — CLI tool, no UI.

### Observability Tests

Not applicable — `OBS-001` is not applicable.

## Definition of Done

- `harness/models.py` `Task` has `seed_files: dict[str, str]` defaulting to `{}`.
- `PiAgentAdapter.run()` writes seed files before invoking pi.
- `_OUTPUT_DIRS` and `_OUTPUT_GLOBS` include `tasks/reviews`.
- `benchmarks/features/review-it.feature` exists with all five required structural scenarios.
- Three task JSON files exist in `benchmarks/tasks/review-it/` with valid `seed_files`.
- `UT-001`, `UT-002`, and `IT-001` pass.
- `uv run python run.py --skill review-it --platform pi-agent --dry-run` completes without error.
- Human reviewer has confirmed that the seeded issue content and code in all three task JSONs accurately represent the intended test scenario (correct implementation, missing AC, missing test coverage).
