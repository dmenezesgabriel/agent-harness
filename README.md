# agent-harness

Small, harness-agnostic skill kit. Every skill follows the [Agent Skills spec](https://github.com/agentskills/agentskills/tree/main/docs) and lives at `skills/<name>/SKILL.md`. Validate all skills with `scripts/validate-skills.sh`.

## Trigger evals

`evals/triggers/run_triggers.py` measures how often each skill triggers on realistic queries. Each query runs `--runs` times in a fresh temp project holding the skills (copied to `.claude/skills/`) plus `evals/triggers/fixtures/`; a run "triggers" when the agent invokes a skill or reads its `SKILL.md` (the spec counts either). A should-trigger query passes at rate > 0.5, a should-not query at < 0.5.

### Prerequisites

- python3 (stdlib only); `uv` for the outcome checks that run the `find-*` scripts
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

- `--split all` over the 84 queries in `queries.json` costs ~252 agent calls at the default `--runs 3`; `app/queries.json` (28 queries, run against the app fixtures below) costs ~84. Run them deliberately.
- `--workers 1 --delay 10` serializes attempts and waits between them; with `--keep-transcripts`, partial progress is saved and later invocations into the same directory accumulate.
- Devin runs invoke `devin -p --export` in each temp project and count `skill` tool calls and reads of a `SKILL.md` (via `read` or `exec`) in the exported ATIF transcript, once per skill per run. `.claude/skills/` is picked up via Devin's claude config import (on by default).

### Scoring and confidence intervals

`--keep-transcripts DIR` appends one line per attempt to `DIR/runs.jsonl` and saves each raw transcript (`.jsonl` for claude, `.json` ATIF for devin, `.err.txt` for failed runs). Aggregate anytime without agent calls:

```bash
python3 -I evals/triggers/run_triggers.py --score-transcripts evals/transcripts/devin-swe2-medium
```

Output is one JSON object per query: `rate`, `ci95` (95% Wilson interval), `errors`, `loaded` (per-skill counts), `passed`. A query is conclusive when its CI sits fully on one side of 0.5, which three runs of one query never reach (3/3 gives [0.44, 1.0], 0/3 gives [0.0, 0.56]); four that all agree do (4/4 gives [0.51, 1.0], 0/4 gives [0.0, 0.49]). To top up straddlers, write a filtered queries file, rerun into the same `DIR`, and re-score — records accumulate.

`--pooled` groups queries that share an `expect` set and reports one CI per group plus `conclusive`; two queries x 3 runs, all hits, give [0.61, 1.0]. Use it to judge a skill, not a single phrasing. With `--invoke`, pass the same skill so its own load is not counted as a hit:

```bash
python3 -I evals/triggers/run_triggers.py --score-transcripts evals/transcripts/devin-2026-11-08-rerun --pooled
```

### Flags and splits

- `--split train|validation|all` — `queries.json` holds the same number of queries, with the same positive/negative mix, in `train` and `validation` (enforced by a runner test). Tune descriptions on `train` only; `validation` is a held-out generalization check, never tune on it.
- `--queries FILE` — alternate query set, e.g. `evals/triggers/fresh.json` or `evals/triggers/app/queries.json`.
- `--fixtures DIR` — project files copied into each sandbox; repeat to layer dirs in order. Default is `evals/triggers/fixtures` (two small smelly files). The realistic app (checkout with a bug, CLI, if/elif notifications, swallowed errors, hollow tests) is `--fixtures evals/triggers/fixtures --fixtures evals/triggers/app/fixtures`.
- `--invoke SKILL` — prefixes every query with `/SKILL`; that skill's own load is not counted (measures post-invocation routing), so a query that expects `SKILL` itself cannot pass under it. Devin appends the query to the skill body with no separator, and at least 3 of 142 invoked runs (all in one run set) answered "what's the task?" instead of reading it; pool runs rather than trusting one.
- `--model MODEL` — default `sonnet`; devin e.g. `swe-2-medium`.
- `--permission-mode MODE` — devin only. In `-p` mode a tool that would prompt is auto-rejected and ends the run mid-turn (the trigger signal is unaffected, but the run's final answer is lost). Pass `smart` when you need complete answers, e.g. for result-quality checks.
- Exit codes: 0 all passed, 1 some failed, 2 bad input.

### Caveats

- The agent runs in your real environment: global skills, user config, hooks, and MCP servers are visible. Any skill load counts on should-not queries — inspect the `loaded` map when one fails.
- Non-interactive runs can't show approval prompts; the skills only need read/exec access to the temp project, which default permissions cover.

### Measured results

All devin `swe-2-medium`, serial with `--delay 10`; transcripts under `evals/transcripts/` (gitignored), re-score with `--score-transcripts DIR [--pooled]`. Pooled groups share an `expect` set; `conclusive` means the 95% CI sits fully on the passing side of 0.5.

**Organic triggering** (nothing invoked):
- `queries.json`, 84 queries x 3 runs (`devin-2026-11-08-rerun`): 84/84 pass; 25 of 32 pooled groups conclusive, none failing.
- `app/queries.json`, 28 queries on the app fixtures (`devin-app-2026-11-09`): 14 pooled groups, all pass, 12 conclusive. The 8 near-miss negatives (tests layout, `except` vs bare `except`, `assertTrue` vs `assertIsNotNone`, ...) load nothing in 24 runs (CI [0, 0.14]). Not conclusive: `find-tautological-assertions` 8/10 (CI [0.49, 0.94]) and one `fix-root-causes` query at 3/4.
- Small feature requests are the weak spot: the router fires on 3/5 (`app-add-slack`, CI [0.23, 0.88]) and 3/4 (`app-json-flag-real`) of runs, against 9/9 for review and refactor requests. The description is deliberately not broadened to catch them, since a wider one would also fire on one-line edits; invoke `/engineering-mode` for those.

**Routing after `/engineering-mode`** (`devin-router-2026-11-09`, `devin-router-app-2026-11-09`): all 27 other skills load through the router at least once. 49/52 leaf queries on `queries.json` reached the expected skill on the first pass (all three misses were dropped queries, see `--invoke`); on the app fixtures all 13 scorable pooled groups pass and 11 are conclusive (the four router-expected queries cannot be scored under `--invoke`). Conceptual negatives load nothing (0/21). Weakest links when judged one skill at a time: `tdd` 4/7, `find-train-wrecks` 5/10 (often `law-of-demeter` loads instead), `find-feature-envy` 3/5. The router's pointer to `tdd` is soft: two of three invoked runs of "write the test before you touch the code" did the work without loading it.

**What the skills change in the work** (`run_outcomes.py`, below). Correct behavior is unchanged by skills: every arm passes the held-out behavior tests (hidden_passes 71/71 across all arms). What changes is how the work is done, and only when the router is invoked.

### Outcome evals

`evals/triggers/run_outcomes.py` runs the same coding tasks in a fresh sandbox of the app fixtures under three arms — `none` (no skills installed), `skills` (installed, the agent decides) and `router` (prompt prefixed with `/engineering-mode`) — then scores each finished project with deterministic checks (`outcome_checks.py`, no LLM judge). Tasks and held-out behavior tests are in `evals/triggers/outcomes/`; the agent never sees the hidden tests.

```bash
python3 -I evals/triggers/run_outcomes.py --runs 4 --keep-transcripts evals/transcripts/devin-outcomes   # 4 tasks x 3 arms x 4 runs
python3 -I evals/triggers/run_outcomes.py --score --keep-transcripts evals/transcripts/devin-outcomes    # re-score, no agent calls
```

Attempts are serial with `--delay 10` and the runner has no `--workers` flag. Each record keeps the agent's diff. Checks: `suite_passes`, `hidden_passes`, `tests_added`, `tests_fail_on_original` (the new test fails once the fix is reverted, not on an import error), `branching_not_increased` (`find-nested-branches`), `no_tautologies`, `no_swallowed_errors`, `mutants_killed`, and `test_first` (a transcript heuristic: first write into `tests/` precedes the first into `src/`).

Results (passes/runs; `devin-outcomes-2026-11-09`, n=8 per cell except `hollow-tests` n=4):

| Check | none | skills | router |
|---|---|---|---|
| `cart-crash` `test_first` | 0/8 | 5/6 | 7/7 |
| `slack-channel` `test_first` | 0/8 | 0/8 | 4/8 |
| `slack-channel` `branching_not_increased` | 0/8 | 1/8 | 4/8 |
| `ingest-errors` `no_swallowed_errors` | 7/8 | 8/8 | 8/8 |
| `hollow-tests` `mutants_killed` | 3/4 | 4/4 | 4/4 |
| any task, `hidden_passes` | all pass | all pass | all pass |

Only the `cart-crash` `test_first` gap is significant (Fisher exact, none vs router p<0.001, vs skills p=0.003); `slack-channel` router vs none is p=0.077. `ingest-errors` has no headroom, since the unaided agent already removes the swallowed handlers 7 of 8 times. In the `skills` arm the agent loads `engineering-mode` but does not act on it for design (1/8), so the design effect needs the router invoked.

A rewrite of the router's phases (scan principles before editing) raised the router arm's design checks from 12/16 to 16/16 but not significantly overall (pooled 21/32 to 25/31, p=0.257) and left the `skills` arm unchanged, so it was not adopted.

### Earlier baselines

Before the current 84-query set (`evals/transcripts/devin-swe2-medium-*`, n=8 per query): every then-shipped query passed, and user-invoked mode routed to the expected leaf (`train-wreck-chain` → law-of-demeter, `arrow-code` → flat-methods, 3/3 each).

The same descriptions trigger far less under `claude -p` sonnet-5-5 (several 0/3 on queries that pass 8/8 under devin), measured on the earlier set and not re-measured: a harness injection-posture difference, not a per-description defect. Treat claude rates as a separate tuning problem before changing descriptions on its evidence.

After the `find-*` skills gained TypeScript/JavaScript/Java/Kotlin support (`evals/transcripts/devin-find-langs`): 6/6 should-trigger queries pass (weakest `review-service-file` 11/16, 0.69, CI [0.44, 0.86]) and 7/7 language-question negatives pass at 0/5 — naming the new languages did not cause false triggers.
