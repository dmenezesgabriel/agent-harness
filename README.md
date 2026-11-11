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

Every check operationalizes a claim from the source the matching skill cites, not a criterion invented for the eval. Each is a proxy, and its limit is listed:

| Check | Skill | Source and claim | Operationalized as | Limit |
|---|---|---|---|---|
| `red_first` | `tdd` | Beck, *Test Driven Development: By Example*: red, "write a little test that doesn't work", before green | a test run between the first `tests/` write and the first `src/` write showed a failure | misses failures read later from a backgrounded run (undercounts) |
| `test_first` | `tdd` | Beck, same: the test comes before the code | first `tests/` write precedes first `src/` write | path only; `red_first` is the stricter form |
| `tests_fail_on_original` | `tdd`, `principle-fix-root-causes` | Hunt & Thomas, *The Pragmatic Programmer*, "Find bugs once": a found bug gets a test that catches it | the new tests fail, not on an import error, once the fix is reverted | needs the fixed file list in the task |
| `hidden_passes`, `suite_passes` | `principle-prove-it-works` | Hunt & Thomas: "Don't assume it — prove it"; Ousterhout: working code is necessary, not sufficient | held-back behavior tests the agent never saw, and the project's own suite, pass | covers only the behaviors the hidden test names |
| `conditionals_not_increased` | `principle-open-closed` | Meyer, *OOSC*: modules open for extension, closed for modification; Martin, *Agile Software Development* ch. 9: extend behavior "by adding new code, not by changing old code that already works", and a type switch that grows per variant is the canonical violation | adding the variant adds no decision point (if/elif/case/ternary) to the dispatching file | a proxy: it does not prove the next variant needs no edit; Martin's "strategic closure" is met here because each task's file already holds three variants when the fourth arrives |
| `branching_not_increased` | `principle-flat-methods` | Bay, *Object Calisthenics*: "don't use the ELSE keyword" | else/elif count does not grow | guard clauses per variant pass it, so it is not an open-closed measure; earlier results that used it as the design check are restated with `conditionals_not_increased` |
| `no_swallowed_errors` | `find-swallowed-errors`, `principle-fix-root-causes` | Hunt & Thomas: "Crash early", "dead programs tell no lies"; Agans, *Debugging* | no handler with an empty or return-only body in the file | a logged-then-ignored error still passes |
| `mutants_killed`, `no_tautologies` | `principle-test-behavior-not-implementation`, `find-tautological-assertions` | Beck, "Test Desiderata": tests are predictive (pass means the code works) and behavioral | the agent's tests catch injected one-line bugs; no assertion compares a value with itself or a constant | a fixed mutant list, not full mutation testing |

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
| `slack-channel` `conditionals_not_increased` | medium | 0/8 | 1/8 | 4/8 |
| | flash | 0/8 | 0/8 | 1/8 |
| `js-shipping-carrier` `conditionals_not_increased` | flash | 0/16 | 0/16 | 12/16 |
| `js-shipping-carrier` `test_first` | flash | 0/16 | 0/16 | 10/16 |
| `hollow-tests` `mutants_killed` | medium (n=4) | 3/4 | 4/4 | 4/4 |
| | flash | 7/8 | 8/8 | 8/8 |

Fisher exact, router vs none: test-first on a bug fix is significant on both models and both languages (`cart-crash` medium p<0.001, flash p<0.001; `js-cart-crash` p<0.001; `ingest-errors` medium p=0.010, flash p<0.001); skills alone also reach it on the two crash tasks (p<0.01) but not on `ingest-errors`. The open-closed effect (`conditionals_not_increased`, rescored from the stored diffs; 2 of the 3 flash `slack-channel` router passes under `branching_not_increased` were one guard clause per variant) is significant in JavaScript (`js-shipping-carrier` 12/16 vs 0/16, p<0.001) and only marginally in Python (`slack-channel` both models pooled 5/16 vs 0/16, p=0.043; flash alone 1/8). Across all stored variant runs (both models, including the rejected router rewrite) the design changes in 22 of 24 runs where `principle-open-closed` loaded and in 5 of 87 where it did not; in the `skills` arm it never loaded organically on flash (0/24), so the effect needs the router invoked. `ingest-errors` swallowed-error removal and `hollow-tests` have little headroom on either model.

A rewrite of the router's phases (scan principles before editing) raised the medium router arm's design checks from 12/16 to 16/16 but not significantly overall (pooled 21/32 to 25/31, p=0.257) and left the `skills` arm unchanged, so it was not adopted.

#### Router A/B on one devin build (flash, 3000.12.43, 2026-11-10)

The tables above ran on build 3000.12.32; comparing a change against them mixed the change with the build, so every arm below ran on the same build, router arm, n=8 per task (timeouts and usage-limit failures excluded and counted). Control = `engineering-mode` before the change (`ab-preC-*`).

| Variant | Design: `conditionals_not_increased` (pix-fee, slack-channel, js-shipping-carrier) | `principle-open-closed` loaded | `ingest-errors` `hidden_passes` | Verdict |
|---|---|---|---|---|
| control | 14/23 (2/8, 4/7, 8/8) | 12/23 | 10/13 | — |
| C: Right step runs every check on edited files and fixes findings | 15/21, p=0.54 | 13/21 | 7/15 | reverted: no design gain |
| C3: Work step loads `principle-open-closed` when a change adds a case to an existing chain, switch, or dispatch | **39/44 (9/14, 15/15, 15/15), p=0.012** | **37/44, p=0.008** | 5/8, p=0.63 | adopted |

C3 hidden tests pass on every completed design run (44/44) and on `cart-crash` 7/7. The `ingest-errors` failures in every arm, control included, are one behavior: the agent changes `load_rows` to return rows plus errors, breaking callers that expect a list (3/8 in the larger control). C first looked like it caused that regression (7/15 vs 13/13 on the older build); the same-build control showed the build does it too.

Without the router (`skills` arm, same build, C3 vs control in interleaved blocks of 4, n=24 each), C3 does not help: `engineering-mode` loaded 12/24 vs 7/24, `principle-open-closed` 2/24 vs 0/24, design 1/24 vs 0/24. These agents answer "add X" in a few steps, matching the existing else-if style, and never reach the Work step's line. With the trigger only in the body, the open-closed effect needs `/engineering-mode` invoked; D below moves it into the description. A description rewrite of `principle-open-closed` (reverted 4d11537) also left organic loading at 1/22.

Organic loads read the body and then skip it: the agent writes the fix before any checklist step. D moves the trigger into `engineering-mode`'s description, which the agent sees before it decides. `skills` arm, same build, n=24 per variant on the three design tasks:

| Variant | `principle-open-closed` loaded | design (`conditionals_not_increased`) | hidden |
|---|---|---|---|
| before C3 | 0/24 | 0/24 | 24/24 |
| C3 (body line) | 2/24 | 1/24 | 24/24 |
| D (C3 + description sentence) | **11/24**, p<0.001 vs before C3 | **6/24**, p=0.022 vs before C3 (p=0.097 vs C3) | 24/24 |

Over-reach checks for D: on `open_closed.json` (written before any change) the six near-miss requests load `principle-open-closed` 0/18 (baseline 0/21) and `engineering-mode` 1/18 (3/21); the positives load open-closed 2/17 (0/22). On the bug-fix tasks open-closed loads 0/16. `cart-crash` `test_first` in the `skills` arm was 8/8 vs 0/8 for `none` (p<0.001) and 4/8 before D (p=0.077); `ingest-errors` hidden 7/8 for both `skills` and `none`. Organic design (6/24) stays far below the invoked router (39/44): agents that load the principle on their own still often keep the `elif`.

Against no skills on the same build (`none` arm, n=24 on the three design tasks: design 0/24, hidden 24/24), `skills` with D reaches 6/24 (p=0.022) and the invoked router 39/44 (p<0.001), with hidden tests unchanged.

A second batch of D (`skills`, n=24) replicated it: design 9/24, open-closed loaded 12/24 (first batch 6/24, 11/24; p=0.53 between batches). Pooled, D reaches design 15/48 vs `none` 0/24 (p=0.001). On the held-out `duration-day` task it does not generalize: `skills` 1/8 vs `none` 0/8, with `engineering-mode` loaded 0/8 and open-closed 1/8. "Add 'day' as a unit" reads as too small to need a skill, so organic triggering depends on how big the request sounds.

E (branch `exp-oc-first-bullet`, not merged) reworded the open-closed "closure is strategic" gotcha after Martin's "take the first bullet", because router pix-fee runs that kept the `elif` quoted it. Router arm, interleaved blocks, n=8: on the held-out `duration-day` task the control already scored 7/8 and E 7/8 (no headroom); on the tuning task pix-fee 6/8 vs 8/8 (p=0.47). Not proven, so not adopted. The 2/8 `duration-day` hidden failures in each arm named the unit `"d"`, copying the file's abbreviations instead of the requested `'day'`.

F (branch `exp-em-request-words`, not merged) replaced D's description sentence with one in request words ("a request to add one more kind of something (a unit, method, type, carrier, channel, or format) ... load principle-open-closed"), because agents choose skills from the request before reading the code. `priority-urgent` was written and committed before F as a second holdout. `skills` arm, interleaved blocks with D on the same build, n=8 per task:

| Task | Variant | `engineering-mode` | open-closed | design | hidden |
|---|---|---|---|---|---|
| `duration-day` (tuning) | D | 4/8 | 3/8 | 3/8 | 8/8 |
| | F | 6/8 | 7/8 (p=0.12) | 5/8 (p=0.62) | 6/8 |
| `priority-urgent` (held out) | D | 3/8 | 3/8 | 2/8 | 8/8 |
| | F | 4/8 | 3/8 | 2/8 (p=1.0) | 8/8 |

F does not move the holdout, and on `open_closed.json` its positives load open-closed 0/18 (D 2/17), with near-misses at 0/18 open-closed and 2/18 `engineering-mode`. Not adopted. D's `duration-day` load rate also changed between runs on the same build (`engineering-mode` 0/8, then 4/8), so n=8 differences on one task are within noise. F's two hidden failures named the unit `"d"`, as in E.

Held-out organic A/B for D (master) against no skills, interleaved blocks on the same build, n=8 per task per arm: `duration-day` design 2/8 vs 0/8 and `priority-urgent` 4/8 vs 0/8 (6/16 vs 0/16, p=0.018); hidden tests 16/16 in both arms. Pooling every D `skills` run on the two holdouts on this build (n=40) against every `none` run (n=24): design 12/40 vs 0/24 (p=0.002), hidden 39/40 vs 24/24. `principle-open-closed` loaded in 15/40 runs. Design passed in 12/15 of those and 0/25 of the rest (p<0.001), so the gain comes from runs that load the principle, and loading, not applying, is the organic bottleneck. These are observational splits: runs that load the skill may also differ in other ways.

The spec predicts this ceiling (`optimizing-descriptions.mdx`): "A simple, one-step request ... may not trigger a ... skill even if the description matches perfectly, because the agent can handle it with basic tools." Both holdouts are one-line requests, and two description rewrites (E, F) did not raise loading against same-build controls. For small changes the measured way to get the skill applied is to invoke `/engineering-mode` (design 39/44, loads every run), not more description tuning.

Per-step attribution of the 40 held-out `skills` runs: `engineering-mode` loaded in 17. When it loaded, open-closed followed in 14/17 and design passed in 11/17. When it did not, open-closed loaded in 1/23 and design passed in 1/23. The router-to-leaf handoff and the leaf's effect both work; the miss is the router's own trigger on one-line requests.

### Earlier baselines

Before the current 84-query set (`evals/transcripts/devin-swe2-medium-*`, n=8 per query): every then-shipped query passed, and user-invoked mode routed to the expected leaf (`train-wreck-chain` → law-of-demeter, `arrow-code` → flat-methods, 3/3 each).

The same descriptions trigger far less under `claude -p` sonnet-5-5 (several 0/3 on queries that pass 8/8 under devin), measured on the earlier set and not re-measured: a harness injection-posture difference, not a per-description defect. Treat claude rates as a separate tuning problem before changing descriptions on its evidence.

After the `find-*` skills gained TypeScript/JavaScript/Java/Kotlin support (`evals/transcripts/devin-find-langs`): 6/6 should-trigger queries pass (weakest `review-service-file` 11/16, 0.69, CI [0.44, 0.86]) and 7/7 language-question negatives pass at 0/5 — naming the new languages did not cause false triggers.
