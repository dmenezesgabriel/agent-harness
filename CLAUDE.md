# agent-harness

Small, harness-agnostic skill kit. Every skill follows the Agent Skills spec; no harness-specific fields.

## Source of truth

https://github.com/agentskills/agentskills/tree/main/docs (`specification.mdx`, `skill-creation/best-practices.mdx`).
Never invent frontmatter fields or layout the spec does not define.

Skill rules that fail validation or review:
- `skills/<name>/SKILL.md`; `name` equals the directory name, `[a-z0-9-]`, ≤64 chars, no leading/trailing/`--` hyphen.
- Frontmatter `description` (≤1024 chars) says what the skill does AND when to use it.
- Body ≤500 lines (our target is far smaller); references one level deep from `SKILL.md`.

## Test skill scripts

```bash
make check                                                  # full gate: pytest+coverage, ruff, pyright (strict), bandit, vulture, radon, xenon, deptry, pip-audit
make commit-check                                           # same gate minus pip-audit (network) — runs in both pre-commit configs
uv run pytest                                               # tests only (includes doctests)
uv run python -I -m unittest discover -s skills/<name>/scripts   # one skill
make mutmut                                                 # mutation testing (slow, run deliberately)
python3 -I -m unittest discover -s skills/<name>/scripts    # no venv: Python paths only, language tests skip
```

`make sync` once per clone. `make <target>` names each stage (test, lint, types, security, deadcode, deps, complexity, audit).

The `find-*` scripts parse Python with the stdlib and TypeScript/JavaScript, Java, and Kotlin with tree-sitter. Each script's PEP 723 header pins `tree-sitter-language-pack` and sets `tool.uv.exclude-newer`, so `uv run` on a script never resolves post-cutoff releases. The root `pyproject.toml`/`uv.lock` pins every tool and dependency by exact version + hash, gates installs to wheels only (`no-build`), and applies the same release cutoff.

## Measure triggering

Spec method (`skill-creation/optimizing-descriptions.mdx`): queries in `evals/triggers/queries.json`, 3 runs each, pass at rate > 0.5 (should-trigger) or < 0.5 (should-not). ~60 real `claude` calls for `all`, so run it deliberately.

```bash
python3 -I -m unittest discover -s evals/triggers          # runner tests, no claude calls
python3 -I evals/triggers/run_triggers.py --split train    # tune descriptions against train only
python3 -I evals/triggers/run_triggers.py --split validation   # check generalization; never tune on it
python3 -I evals/triggers/run_triggers.py --queries evals/triggers/fresh.json --invoke engineering-mode   # final check on never-tuned queries
python3 -I evals/triggers/run_triggers.py --harness devin --model swe-2-medium --workers 1 --delay 10 --keep-transcripts evals/transcripts/devin   # run under devin, serial + paced; re-score with --score-transcripts <dir>
```

JSON line per query on stdout, summary on stderr. Exit 0 all passed, 1 some failed, 2 bad input.

## Validate skills

One command, from the repo root:

```bash
scripts/validate-skills.sh                 # all skills
scripts/validate-skills.sh skills/<name>   # one skill
```

Exit 0 = every skill valid; 1 = a skill failed (reason printed); 2 = validator not installed.
Run it after every skill change, before committing.

Two opt-in pre-commit setups run `make commit-check` plus skill validation, check that the message is a Conventional Commit (`cz check`; the type decides the release, see README "Install and update"), and block the commit on failure. CI (`.github/workflows/ci.yml`) runs the full `make check`, skill validation and the same message check, then releases from `master`:

```bash
git config core.hooksPath .githooks   # repo hook (warns and skips when validator/make is missing)
pre-commit install                  # or the pre-commit framework, .pre-commit-config.yaml
```

### Validator setup (once per clone; `research_repos/` is gitignored)

`skills-ref` is the spec's reference validator (demo-grade, 536 lines, deps: click, strictyaml). Pinned to agentskills commit `69ef37e`.

```bash
scripts/install-validator.sh   # sparse clone at the pinned commit, `uv sync --locked`; CI runs the same script
```

`research_repos/pstack` is a read-only reference (cursor/plugins `pstack`); do not copy its Cursor-specific names or fields.
