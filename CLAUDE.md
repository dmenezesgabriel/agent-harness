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
python3 -I -m unittest discover -s skills/<name>/scripts
```

## Measure triggering

Spec method (`skill-creation/optimizing-descriptions.mdx`): queries in `evals/triggers/queries.json`, 3 runs each, pass at rate > 0.5 (should-trigger) or < 0.5 (should-not). ~60 real `claude` calls for `all`, so run it deliberately.

```bash
python3 -I -m unittest discover -s evals/triggers          # runner tests, no claude calls
python3 -I evals/triggers/run_triggers.py --split train    # tune descriptions against train only
python3 -I evals/triggers/run_triggers.py --split validation   # check generalization; never tune on it
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

### Validator setup (once per clone; `research_repos/` is gitignored)

`skills-ref` is the spec's reference validator (demo-grade, 536 lines, deps: click, strictyaml). Pinned to agentskills commit `69ef37e`.

```bash
cd research_repos
git clone --filter=blob:none --sparse https://github.com/agentskills/agentskills.git _as
git -C _as checkout 69ef37e9424c0a7ea9dd2293b559e43ec8176379
git -C _as sparse-checkout set skills-ref
mv _as/skills-ref skills-ref && rm -rf _as
cd skills-ref && uv sync
```

`research_repos/pstack` is a read-only reference (cursor/plugins `pstack`); do not copy its Cursor-specific names or fields.
