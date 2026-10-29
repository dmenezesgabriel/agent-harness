# agent-harness

Small, harness-agnostic skill kit. Every skill follows the [Agent Skills spec](https://github.com/agentskills/agentskills/tree/main/docs) and lives at `skills/<name>/SKILL.md`. Validate all skills with `scripts/validate-skills.sh`.

## Trigger evals

`evals/triggers/run_triggers.py` measures how often each skill triggers on realistic queries. Each query runs `--runs` times in a fresh temp project holding the skills (copied to `.claude/skills/`) plus `evals/triggers/fixtures/`; a run "triggers" when the agent invokes a skill. A should-trigger query passes at rate > 0.5, a should-not query at < 0.5.

### Prerequisites

- python3 (stdlib only)
- `claude` CLI for `--harness claude` (default), or `devin` CLI logged in (`devin auth status`) for `--harness devin`

### Runner tests (no agent calls)

```bash
python3 -I -m unittest discover -s evals/triggers
```

### Running

Claude (the default harness):

```bash
python3 -I evals/triggers/run_triggers.py --split train
```

Devin at a fixed model/effort — serial and paced to stay under rate limits:

```bash
python3 -I evals/triggers/run_triggers.py --harness devin --model swe-2-medium \
  --runs 8 --workers 1 --delay 10 --keep-transcripts evals/transcripts/devin-swe2-medium
```

- `--split all` over the 20 shipped queries costs ~60 agent calls at the default `--runs 3`. Run it deliberately.
- `--workers 1 --delay 10` serializes attempts and waits between them; with `--keep-transcripts`, partial progress is saved and later invocations into the same directory accumulate.
- Devin runs invoke `devin -p --export` in each temp project and count `skill` tool calls in the exported ATIF transcript. `.claude/skills/` is picked up via Devin's claude config import (on by default).

### Scoring and confidence intervals

`--keep-transcripts DIR` appends one line per attempt to `DIR/runs.jsonl` and saves each raw transcript (`.jsonl` for claude, `.json` ATIF for devin, `.err.txt` for failed runs). Aggregate anytime without agent calls:

```bash
python3 -I evals/triggers/run_triggers.py --score-transcripts evals/transcripts/devin-swe2-medium
```

Output is one JSON object per query: `rate`, `ci95` (95% Wilson interval), `errors`, `loaded` (per-skill counts), `passed`. A query is conclusive when its CI sits fully on one side of 0.5. To top up straddlers, write a filtered queries file, rerun into the same `DIR`, and re-score — records accumulate.

### Flags and splits

- `--split train|validation|all` — `queries.json` holds equal counts of should-trigger and should-not queries per split (enforced by a runner test). Tune descriptions on `train` only; `validation` is a held-out generalization check, never tune on it.
- `--queries FILE` — alternate query set, e.g. `evals/triggers/fresh.json`.
- `--invoke SKILL` — prefixes every query with `/SKILL`; that skill's own load is not counted (measures post-invocation routing).
- `--model MODEL` — default `sonnet`; devin e.g. `swe-2-medium`.
- `--permission-mode MODE` — devin only. In `-p` mode a tool that would prompt is auto-rejected and ends the run mid-turn (the trigger signal is unaffected, but the run's final answer is lost). Pass `smart` when you need complete answers, e.g. for result-quality checks.
- Exit codes: 0 all passed, 1 some failed, 2 bad input.

### Caveats

- The agent runs in your real environment: global skills, user config, hooks, and MCP servers are visible. Any skill load counts on should-not queries — inspect the `loaded` map when one fails.
- Non-interactive runs can't show approval prompts; the skills only need read/exec access to the temp project, which default permissions cover.

### Measured baseline

Devin `swe-2-medium`, n=8 per query (`evals/transcripts/devin-swe2-medium-*`, re-score with `--score-transcripts`): every shipped query passes — should-trigger at rate 1.0, should-not at 0. `engineering-mode` co-fires with the expected leaf on most should-trigger runs rather than racing it; user-invoked mode routes to the expected leaf (`train-wreck-chain` → law-of-demeter, `arrow-code` → flat-methods, 3/3 each). Weakest measured trigger: `em-add-json-flag` at 11/16 (0.69, CI [0.44, 0.86]) — a bare feature request with no design cues.

The same descriptions trigger far less under `claude -p` sonnet-5-5 (several 0/3 on queries that pass 8/8 under devin): a harness injection-posture difference, not a per-description defect. Treat claude rates as a separate tuning problem before changing descriptions on its evidence.

After the `find-*` skills gained TypeScript/JavaScript/Java/Kotlin support (`evals/transcripts/devin-find-langs`): 6/6 should-trigger queries pass (weakest `review-service-file` 11/16, 0.69, CI [0.44, 0.86]) and 7/7 language-question negatives pass at 0/5 — naming the new languages did not cause false triggers.
