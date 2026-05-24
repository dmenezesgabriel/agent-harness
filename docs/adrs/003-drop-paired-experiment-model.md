---
id: "003"
created: 2026-05-23
updated: 2026-05-23
status: Accepted
---

# ADR 003: Drop Paired A/B Experiment Model in Favor of Single-Execution Structural Validation

## Status

Accepted

## Context

The harness was built around a paired experiment model: run N trials under `WITH_SKILL` and N trials under `WITHOUT_SKILL`, then apply Wilcoxon signed-rank and Cohen's d to test whether the skill makes a measurable difference.

This model has two fundamental problems:

1. **Statistical threshold is never met.** Wilcoxon requires n≥5 paired samples to return a meaningful p-value. The default is n=3. `analysis.py` itself notes this: at n<5 it returns `p=1.0, significant=False` unconditionally. Every default run produces noise, not signal.

2. **Wrong question for prompt templates.** Skills are prompt templates, not learned weights. The relevant question is not "is the skill better than no skill?" (which requires population-level comparison) but "does the agent follow the skill's intended workflow?" — which is a deterministic structural check on a single output.

The paired model doubles token cost (2 conditions × N trials) and produces statistics that are always insignificant at default settings.

## Decision

Drop the paired experiment model entirely. Replace with single-execution structural validation:

- Remove `Condition` enum (`WITH_SKILL`, `WITHOUT_SKILL`).
- Remove `n_trials` loop. Execute each task once.
- Remove `TrialStats`, Wilcoxon signed-rank, and Cohen's d (`analysis.py` deleted).
- Replace `TrialResult` (trial-centric) with `TaskResult` (run-centric): drop `condition` and `trial_index` fields.
- Replace `ExperimentSummary` (paired comparison) with `RunSummary` (single-pass aggregation): drop `without_skill`, `p_values`, `effect_sizes`, and `trial_stats`.
- Champion/challenger comparison continues via `--skill-dir` variant runs, comparing skill-v1 against skill-v2 rather than skill against no-skill.

## Consequences

**Positive**

- Token cost drops by ~6× (3 trials × 2 conditions → 1 execution per task).
- Models, runner, and CLI become significantly simpler.
- Evaluator pipeline decouples from experiment design.
- Tests no longer depend on `Condition` enum values — a volatile string constant.

**Negative**

- No built-in comparison against "no-skill" baseline. Champion comparisons are skill-vs-skill only.
- Historical MLflow runs using `condition`, `trial_index`, and `without_skill__*` metric keys become incompatible with new `RunSummary` schema.

**Neutral**

- `behave_pass_rate` and `quality_score` remain the primary promotion signals for `bench-promote`.
- `LLMJudge` is preserved as a standalone callable but removed from the core runner loop.
