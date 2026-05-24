# Project Context

This file defines the domain vocabulary for this project. Skills read it at session start to use consistent terminology in task names, requirements, acceptance criteria, test names, and code.

Update this file when a domain term is first defined or clarified. Do not batch updates — add terms as they emerge.

---

## Domain terms

### Skill

**Definition**: A packaged system prompt (SKILL.md + references + assets) that instructs an agent how to perform a structured software engineering workflow (e.g., plan-it, implement-it, review-it).
**Usage**: `skill_name` parameter in CLI flags, `harness/skill_loader.py`, task corpus file `"skill"` field.
**Constraints**: Each skill lives under `skills/<name>/` and is installed to agent tool directories by `scripts/install-skills.sh`.

### Task (benchmark task)

**Definition**: A single benchmark item stored as a JSON file in `tasks/plan-it/` or `tasks/implement-it/`, describing an instruction, a codebase context, a gold standard, and an evaluator type.
**Usage**: `Task` dataclass in `harness/models.py`; loaded by `harness/runner.py` per experiment.
**Constraints**: Tasks are immutable corpus items; they are not modified during experiments.

### TaskResult

**Definition**: One execution of a single Task (with the skill), producing a `TaskResult` with timing, token counts, output, workspace snapshot, and metrics.
**Usage**: `TaskResult` dataclass in `harness/models.py`; logged by `Tracker.log_result()`.

### RunSummary

**Definition**: Aggregated metrics for all tasks run in a benchmark, containing mean ± std for each metric.
**Usage**: `RunSummary` dataclass in `harness/models.py`; orchestrated by `harness/runner.py`; logged by `Tracker.log_summary()`.

### Adapter

**Definition**: A platform-specific implementation of `AgentAdapter` that invokes a specific agent CLI (claude, pi, opencode) in an isolated workspace and returns a `TaskResult`.
**Usage**: `AgentAdapter` ABC in `harness/adapters/base.py`; concrete classes in `harness/adapters/`.
**Constraints**: Each adapter must isolate its trial in a temporary workspace via `WorkspaceManager`.

### Evaluator

**Definition**: A metric-computing implementation of `Evaluator` that scores a `TaskResult` against a Task's gold standard and writes domain-specific scores (`accuracy`, `quality_score`, `behave_pass_rate`, `test_pass_rate`, `judge_score`) directly onto the result. Precision, recall, and F1 are not computed — the observation count per run is too small for those metrics to be meaningful.
**Usage**: `Evaluator` ABC in `harness/evaluators/base.py`; concrete classes in `harness/evaluators/`.

### Tracker

**Definition**: A backend-specific implementation of `Tracker` that persists task result and run summary data to an observability system (e.g., MLflow). `NullTracker` is the no-op implementation used in dry runs and tests.
**Usage**: `Tracker` ABC in `harness/tracking/base.py`; `MLflowTracker` in `harness/tracking/tracker.py`.

### WorkspaceManager

**Definition**: An injectable abstraction over temporary directory creation, git initialization, file snapshotting, and cleanup. `TempWorkspaceManager` wraps real filesystem operations; `FakeWorkspaceManager` is used in tests.
**Usage**: `WorkspaceManager` ABC in `harness/adapters/workspace.py`.

### Champion

**Definition**: The skill variant (identified by content hash) that has achieved the highest benchmark score for a given skill and is marked as the reference point for future comparisons.
**Usage**: `bench-promote` CLI command; stored in `skills-lock.json`.

### Registry

**Definition**: An in-memory `dict`-backed lookup table that maps string names (e.g., `"claude-code"`, `"plan"`) to component factories, enabling new adapters and evaluators to be added without modifying the runner.
**Usage**: `Registry[T]` in `harness/registry.py`; `adapter_registry` and `evaluator_registry` module singletons.

---

## Decisions and constraints

### Interface mechanism

All harness extension points (`AgentAdapter`, `Evaluator`, `Tracker`, `WorkspaceManager`) use Python abstract base classes (`abc.ABC`). See ADR `docs/adrs/002-extension-point-interface-mechanism.md`.

### Single-execution model

Each benchmark run executes every Task once with the skill. There is no `WITHOUT_SKILL` condition, no statistical significance testing, and no paired comparison. See ADR `docs/adrs/003-drop-paired-experiment-model.md`.

### Workspace isolation

Each TaskResult is produced in a freshly created temp directory with `git init` pre-applied. The agent's output files are captured via `WorkspaceManager.snapshot_workspace()` before cleanup.

---

### Scaffolding files

**Definition**: Pre-existing files copied into the trial workspace by the adapter (e.g., `opencode.json`, all files under `skills/`) that are present before the agent runs and should be excluded from the workspace snapshot to isolate agent-created output.
**Usage**: `OpenCodeAdapter._parse_output()` workspace diff; `WorkspaceManager.snapshot_workspace()` filtering.
**Constraints**: Scaffolding files are identified by comparing "before" and "after" snapshots; files present with identical content in both are excluded.

---

## Out of scope

- Multi-tenant or multi-user benchmarking — all experiments are single-user local runs.
- Real-time streaming of trial output — results are captured after agent completion.
- Automated skill promotion — promotion requires explicit human invocation of `bench-promote`.
