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
- `--invoke SKILL` — prefixes every query with `/SKILL`; that skill's own load is not counted (measures post-invocation routing), so a query that expects `SKILL` itself cannot pass under it. Devin appends the query to the skill body with no separator (right after its last sentence), and some runs answer "what's the task?" instead of reading it: medium 2 of 142 invoked runs, flash 16 of 276, all on three short imperative queries (`taut-scan` 8/8, `vu-stacked-prs` 5/6, `deep-chains` 3/7) that read like one more rule of the skill; queries with concrete context ("Our invoice code does ...") were never dropped. A dropped run counts as a miss, so check the final answers of a failing invoked query before blaming the router.
- `--model MODEL` — default `sonnet`; devin e.g. `swe-2-medium`.
- `--permission-mode MODE` — devin only. In `-p` mode a tool that would prompt is auto-rejected and ends the run mid-turn (the trigger signal is unaffected, but the run's final answer is lost). Pass `smart` when you need complete answers, e.g. for result-quality checks.
- Exit codes: 0 all passed, 1 some failed, 2 bad input.

### Caveats

- The agent runs in your real environment: global skills, user config, hooks, and MCP servers are visible. Any skill load counts on should-not queries — inspect the `loaded` map when one fails.
- Non-interactive runs can't show approval prompts; the skills only need read/exec access to the temp project, which default permissions cover.

### Measured results

Devin, serial with `--delay 10`, on two models: `swe-2-medium` (2026-11-08/09) and `swe-2-flash-medium` (2026-11-09/10, `flash-*` dirs). Transcripts under `evals/transcripts/` (gitignored); re-score with `--score-transcripts DIR [--pooled]`. Pooled groups share an `expect` set; `conclusive` means the 95% CI sits fully on the passing side of 0.5. The agent runs in the real environment, including a host hook (`devjob-guard`) that rejects heavy commands until the agent retries with a bypass; it hits every arm alike but adds steps.

**Organic triggering** (nothing invoked):
- `queries.json`, 84 queries x 3 runs. Medium (`devin-2026-11-08-rerun`): 84/84 pass, 25 of 32 pooled groups conclusive. Flash (`flash-2026-11-09`): 79/84, 30 of 32 groups pass, 20 conclusive; all five misses are should-trigger validation queries, three of them at 1/2 after a timeout (`magic-constants`, `special-case-branch`, `pw-reset-flow`), plus `billing-breaks` and `sub-csv-branch` at 1/3.
- `app/queries.json`, 28 queries on the app fixtures. Medium (`devin-app-2026-11-09`): 14 groups pass, 12 conclusive. Flash (`flash-app-2026-11-09`): 12 of 14 pass; topped up to 8 runs (7 after a timeout each), `app-rows-dropped` loads its skills in 2/7 and `app-readonly-repo` in 2/7 (both CI [0.08, 0.64]), so organic triggering on these two debugging questions is weak on flash. On both models the 8 near-miss negatives (tests layout, `except` vs bare `except`, `assertTrue` vs `assertIsNotNone`, ...) load nothing in 24 runs (CI [0, 0.14]).
- Small feature requests are the weak spot on medium: the router fires on 3/5 (`app-add-slack`) and 3/4 (`app-json-flag-real`), against 9/9 for review and refactor requests (flash: 10/11 over the four router queries). The description is deliberately not broadened to catch them, since a wider one would also fire on one-line edits; invoke `/engineering-mode` for those.

**Routing after `/engineering-mode`**: all 27 other skills load through the router at least once on both models. Medium (`devin-router-2026-11-09`, `devin-router-app-2026-11-09`): 49/52 leaf queries reached the expected skill on the first pass (all three misses were dropped queries, see `--invoke`); on the app fixtures all 13 scorable groups pass, 11 conclusive; conceptual negatives load nothing (0/21). Flash (`flash-router-2026-11-09`, `flash-router-app-2026-11-09`; the weak queries topped up to 8 runs on 2026-11-10): 28 of 30 leaf groups pass (22 conclusive) and 13 of 13 on the app. The two failing groups fail on dropped queries (see `--invoke`), not routing: `find-tautological-assertions` 3/11, but 3/3 on runs that saw the task; `find-train-wrecks` 2/7, but on the 4 runs that saw the task 2 read its `SKILL.md` and 2 ran its script directly (not counted as a load); `principle-sequence-verifiable-units` passes at 7/12, 7/7 on runs that saw the task. Negatives: 1/15 runs on `queries.json`; on the app 5/28, all on "read `cart['items'][2]['qty']` without a KeyError" (5/8 load `law-of-demeter`, 4/8 `domain-types-over-primitives`), a real over-load after the router. `tdd`: medium 4/7, flash 6/6.

**What the skills change in the work** (`run_outcomes.py`, below): how the work is done, mostly when the router is invoked. On medium every arm passed the held-out behavior tests (71/71); on flash the only behavior failures are in the unaided arms of `ingest-errors` (none 6/8, skills 7/8, router 8/8).

### Outcome evals

`evals/triggers/run_outcomes.py` runs the same coding tasks in a fresh sandbox of the app fixtures under three arms — `none` (no skills installed), `skills` (installed, the agent decides) and `router` (prompt prefixed with `/engineering-mode`) — then scores each finished project with deterministic checks (`outcome_checks.py`, no LLM judge). Tasks and held-out behavior tests are in `evals/triggers/outcomes/`; the agent never sees the hidden tests. The `js-*` tasks add a small JavaScript app (`outcomes/js_fixtures/`, its own fixture layer, so the Python tasks' sandbox is unchanged) tested with `node --test`.

```bash
python3 -I evals/triggers/run_outcomes.py --model swe-2-flash-medium --runs 8 --keep-transcripts evals/transcripts/flash-outcomes   # 6 tasks x 3 arms x 8 runs
python3 -I evals/triggers/run_outcomes.py --score --keep-transcripts evals/transcripts/flash-outcomes    # re-score, no agent calls
```

Attempts are serial with `--delay 10` and the runner has no `--workers` flag. Each record keeps the agent's diff. Checks: `suite_passes`, `hidden_passes`, `tests_added`, `tests_fail_on_original` (the new test fails once the fix is reverted, not on an import error), `branching_not_increased` (`find-nested-branches`), `no_tautologies`, `no_swallowed_errors`, `mutants_killed`, and two transcript heuristics: `test_first` (the first write into `tests/` precedes the first into `src/`) and the stricter `red_first` (a unittest/pytest/`node --test` run between those two writes showed a failure). Requires `uv` (the checks run the `find-*` scripts) and `node` for the `js-*` tasks. Attempts that time out are recorded as errors and left out; under host load, cells that lost runs were topped up to n=8 with `--timeout 900`.

Results, passes/runs, n=8 per cell unless shown (medium `devin-outcomes-2026-11-09`; flash `flash-outcomes-2026-11-09`, and for `js-*` that dir plus `flash-outcomes-js-2026-11-09`, two independent batches of 8):

| Check | model | none | skills | router |
|---|---|---|---|---|
| `cart-crash` `test_first` | medium | 0/8 | 5/6 | 7/7 |
| | flash | 0/8 | 7/8 | 8/8 |
| `cart-crash` `red_first` | medium | 0/8 | 5/6 | 5/7 |
| | flash | 0/8 | 7/8 | 6/8 |
| `js-cart-crash` `test_first` | flash | 0/15 | 12/16 | 16/16 |
| `js-cart-crash` `red_first` | flash | 0/15 | 12/16 | 15/16 |
| `ingest-errors` `test_first` | medium | 0/6 | 2/7 | 6/8 |
| | flash | 0/8 | 2/8 | 8/8 |
| `ingest-errors` `no_swallowed_errors` | medium | 7/8 | 8/8 | 8/8 |
| | flash | 6/8 | 7/8 | 8/8 |
| `slack-channel` `test_first` | medium | 0/8 | 0/8 | 4/8 |
| | flash | 0/8 | 0/8 | 4/8 |
| `slack-channel` `branching_not_increased` | medium | 0/8 | 1/8 | 4/8 |
| | flash | 0/8 | 1/8 | 3/8 |
| `js-shipping-carrier` `branching_not_increased` | flash | 0/16 | 0/16 | 12/16 |
| `js-shipping-carrier` `test_first` | flash | 0/16 | 0/16 | 10/16 |
| `hollow-tests` `mutants_killed` | medium (n=4) | 3/4 | 4/4 | 4/4 |
| | flash | 7/8 | 8/8 | 8/8 |

Fisher exact, router vs none: test-first on a bug fix is significant on both models and both languages (`cart-crash` medium p<0.001, flash p<0.001; `js-cart-crash` p<0.001; `ingest-errors` medium p=0.010, flash p<0.001); skills alone also reach it on the two crash tasks (p<0.01) but not on `ingest-errors`. The design effect, not adding another branch for a new variant, is significant in JavaScript (`js-shipping-carrier` 12/16 vs 0/16, p<0.001) and for Python only with both models pooled (`slack-channel` 7/16 vs 0/16, p=0.007; per model p=0.077 and p=0.20). In the `skills` arm the agent loads `engineering-mode` but rarely acts on it for design (2/32 across both models and both variant tasks), so the design effect needs the router invoked. `ingest-errors` swallowed-error removal and `hollow-tests` have little headroom on either model.

A rewrite of the router's phases (scan principles before editing) raised the medium router arm's design checks from 12/16 to 16/16 but not significantly overall (pooled 21/32 to 25/31, p=0.257) and left the `skills` arm unchanged, so it was not adopted.

### Earlier baselines

Before the current 84-query set (`evals/transcripts/devin-swe2-medium-*`, n=8 per query): every then-shipped query passed, and user-invoked mode routed to the expected leaf (`train-wreck-chain` → law-of-demeter, `arrow-code` → flat-methods, 3/3 each).

The same descriptions trigger far less under `claude -p` sonnet-5-5 (several 0/3 on queries that pass 8/8 under devin), measured on the earlier set and not re-measured: a harness injection-posture difference, not a per-description defect. Treat claude rates as a separate tuning problem before changing descriptions on its evidence.

After the `find-*` skills gained TypeScript/JavaScript/Java/Kotlin support (`evals/transcripts/devin-find-langs`): 6/6 should-trigger queries pass (weakest `review-service-file` 11/16, 0.69, CI [0.44, 0.86]) and 7/7 language-question negatives pass at 0/5 — naming the new languages did not cause false triggers.
