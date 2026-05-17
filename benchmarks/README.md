# Skills Benchmarking Framework

Answers two questions:
1. **Are skills worth it?** — Do agents produce measurably better outputs when a skill is active vs. not?
2. **Which version is better?** — If you edit a skill, does the new version actually improve results?

## How experiments work

**Paired experiment** — same task, two conditions:

| Condition | pi agent | Claude Code | OpenCode |
|---|---|---|---|
| **with skill** | `pi --skill skills/plan-it "..."` | `claude --print "/plan-it ..."` | `opencode run "..."` (skills auto-loaded) |
| **without skill** | `pi --no-skills "..."` | `claude --print "..."` (no slash command) | `opencode run --pure "..."` |

Same model, same task, same codebase context — only the skill presence differs. This isolates exactly what the skill contributes.

**Non-determinism**: each cell runs `N` trials (default 3, recommended 10 for reliable conclusions). Metrics reported as `mean ± std`.

**Statistical test**: Wilcoxon signed-rank (paired, non-parametric). Effect size: Cohen's d.

## Metrics

| Metric | Definition | Skills |
|---|---|---|
| **Accuracy** | Fraction of tasks where output fully satisfies all required criteria | all |
| **Precision** | TP / (TP+FP) at finding level | plan-it, review skills |
| **Recall** | TP / (TP+FN) — did the output cover all required elements? | plan-it, review skills |
| **F1** | Harmonic mean of precision and recall | all |
| **Quality Score** | Rubric composite (0–10): completeness, testable criteria, HITL classification | plan-it |
| **Test Pass Rate** | Pre-written tests execute and pass against generated code | implement-it |
| **Judge Score** | LLM-as-judge (0–10), `claude-haiku` used to avoid self-enhancement bias | all (opt-in) |
| **Latency (ms)** | Wall-clock time from invocation to final output | all |
| **Token consumption** | Input + output tokens per invocation | all |

## Quick start

```bash
cd benchmarks
uv sync                  # install dependencies (one-time)

# Test plan-it on pi agent, 3 trials per task
uv run python run.py --skill plan-it --platform pi-agent --trials 3

# Same for Claude Code
uv run python run.py --skill plan-it --platform claude-code --trials 3

# implement-it with executable test verification
uv run python run.py --skill implement-it --platform pi-agent --trials 3

# Single task only (faster iteration)
uv run python run.py --skill plan-it --platform pi-agent --trials 1 --task-ids plan-it-001

# With LLM judge
uv run python run.py --skill plan-it --platform pi-agent --trials 5 --judge

# Compare results across platforms
uv run python report.py --skill plan-it --platforms pi-agent,claude-code,opencode

# Launch MLflow dashboard
mlflow ui --backend-store-uri file://./mlruns
```

## Fine-tuning a skill

This is how you experiment with skill improvements:

```bash
# 1. Get baseline with current skill
uv run python run.py --skill plan-it --platform pi-agent --trials 5

# 2. Copy the skill and modify it
cp -r ../skills/plan-it ../skills/plan-it-v2
# ... edit ../skills/plan-it-v2/SKILL.md or its references ...

# 3. Run the variant — tagged separately in MLflow
uv run python run.py --skill plan-it --platform pi-agent --trials 5 \
  --skill-dir ../skills/plan-it-v2

# 4. Compare in MLflow UI
# Filter by: skill=plan-it, platform=pi-agent
# Compare runs tagged skill_variant=../skills/plan-it-v2 vs untagged (baseline)
```

Each run is tagged with `skill_variant` in MLflow, so you can query and compare any number of iterations side by side.

## Task corpus

Tasks live in `tasks/<skill>/NNN-<name>.json`. Schema:

```json
{
  "id": "plan-it-001",
  "skill": "plan-it",
  "title": "Human-readable title",
  "complexity": "single-file | multi-file",
  "language": "python | typescript | ...",
  "instruction": "The exact prompt given to the agent.",
  "codebase_context": "Inline code/file structure context (optional).",
  "gold_standard": {
    "required_sections": ["Context", "Requirements", "Acceptance Criteria", "Tests"],
    "test_commands": ["python3 -c \"from solution_0 import X; assert ...; print('ALL PASS')\""]
  },
  "evaluator": "plan_evaluator | code_evaluator",
  "tags": ["feature", "multi-task"]
}
```

### Current corpus

| Skill | Tasks | Evaluator |
|---|---|---|
| `plan-it` | 5 (001–005) | `plan_evaluator` — structural completeness + rubric |
| `implement-it` | 5 (001–005) | `code_evaluator` — test execution pass rate |

For statistically reliable results at 95% CI: 100+ tasks (minimum), 322 tasks (ideal).

## Adding tasks

For `plan-it`: add to `gold_standard.required_sections` the headings the plan must contain.

For `implement-it`: write `test_commands` as self-contained `python3 -c "..."` that import from `solution_0.py` and print `ALL PASS` on success. The code evaluator writes each fenced code block from the output to `solution_0.py`, `solution_1.py`, etc. in a temp directory, then runs the commands.

## Corpus quality check (from Benchmark² paper)

Before trusting results, verify the corpus is actually discriminating:

```bash
uv run python corpus_qc.py --skill plan-it --platform pi-agent
```

| Metric | Threshold | Meaning |
|---|---|---|
| DS (Discriminability Score) | > 0.2 | Tasks distinguish with vs without skill |
| CAD (Capability Alignment Deviation) | > 0.6 | Hard tasks are consistently hard |
| CBRC (Cross-Benchmark Ranking Consistency) | > 0.4 | Results consistent across subsets |
| BQS (Benchmark Quality Score) | > 0.4 | Overall corpus fitness |
