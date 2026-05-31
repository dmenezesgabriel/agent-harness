---
name: skill-evaluator
description: >
  Evaluates a named skill by running its artifact checks and optionally invoking
  the skill against fixture inputs. Produces a structured eval report with three
  layers: deterministic structural checks (behave), LLM-as-judge qualitative checks,
  and skill input size measurement.
  Use when asked to "evaluate a skill", "check skill output quality",
  "run evals for plan-it", "validate the dataviz skill", or "measure skill input size".
compatibility: Requires Python 3.11+, uv, claude CLI.
metadata:
  domain: skill-evaluation
  version: "1.0"
---

Evaluate the quality and correctness of a skill's output artifacts.

Every structural check must produce a boolean pass/fail by inspecting artifact text —
no subjective interpretation. LLM-as-judge checks are reserved for qualities that cannot
be expressed as patterns, and must use rubrics already defined in `evals/rubrics/`.

## When NOT to use this skill

- The user wants to edit or improve a skill — use plan-it or implement-it instead.
- The user wants a code review of the evaluator runner — use review-it.
- No `evals/` directory exists for the target skill.

## Evaluation modes

| Mode | What it does | Requires |
|------|-------------|----------|
| `invoke` | Calls the skill (haiku) via claude CLI, runs behave structural checks on live output, reports skill input size (char counts). | `claude` CLI |
| `judge` | Runs LLM-as-judge (sonnet) against rubric files on golden fixtures. Reproducible — no agent call needed. | `claude` CLI |
| `all` | Runs invoke → structural → judge in sequence. | `claude` CLI |

Note: The claude CLI does not expose token counts. Skill input size reports character counts for `SKILL.md` and `fixtures/input_*.md` as an honest proxy. This helps compare whether the same or better output quality can be achieved with smaller skill instructions or fixture prompts.

Default: `invoke`.

## Core workflow

### Phase 0: Identify scope

Determine:
1. Which skill(s) to evaluate. If the user names one (e.g. "evaluate plan-it"), use that.
   If they say "all skills" or don't specify, evaluate all skills that have an `evals/` directory.
2. Which mode. Default to `invoke` and state the assumption if not specified.

### Phase 1: Confirm prerequisites

Check before running:

```bash
# Verify uv is available
uv --version

# Verify the runner exists
ls skills/skill-evaluator/runner/runner/run.py

# Verify feature files exist for the target skill
ls skills/<skill-name>/evals/*.feature
```

For `invoke`, `judge`, or `all` mode:
```bash
# claude CLI is required
claude --version
```

If a prerequisite is missing, stop and report exactly what is missing. Do not proceed.

### Phase 2: Run the evaluator

From the repo root:

```bash
cd skills/skill-evaluator/runner
uv run python -m runner.run --skill <skill-name> --mode <mode>
```

To evaluate all skills (invoke mode by default):
```bash
cd skills/skill-evaluator/runner
uv run python -m runner.run
```

Capture the exit code. Non-zero means at least one check failed.

### Phase 3: Surface the report

The runner writes a report to `skills/<skill-name>/evals/reports/<skill-name>-<YYYY-MM-DDTHH-MM-SS-ffffff>.md`.

Read and present:
1. **Structural failures** — which scenario failed, which file, what was missing or wrong.
2. **Judge results** — rubric id, score, result, and reasoning for every verdict (pass and fail). A passing verdict with weak reasoning is a signal the rubric needs tightening.
3. **Skill input size** — char counts for `SKILL.md` and fixture prompts. Compare this with pass rate and judge scores to identify leaner skill instructions that preserve quality.
4. **Pass rate** — overall percentage.

### Phase 4: Interpret and recommend

For each failure:
- Structural: point to the exact rule in the skill's reference files that is violated.
- Judge: suggest whether the SKILL.md guidance is unclear or the artifact is genuinely poor quality.

Do not recommend changes to rubric pass thresholds as a fix — address the underlying skill or artifact.

## Before marking complete

- [ ] Exit code captured — non-zero surfaced to user as a failure
- [ ] Every FAIL entry includes the failing artifact and the specific violated rule
- [ ] Skill input size reported
- [ ] No rubric criteria invented outside the skill's own reference files

## Anti-patterns to avoid

- Do not run judge mode when only structural was requested — it burns tokens unnecessarily.
- Do not surface Claude's conversational output as an artifact — only written files count.
- Do not skip Phase 1 prerequisite checks — missing feature files cause silent passes.
- Do not lower rubric pass thresholds to make failing verdicts pass.
