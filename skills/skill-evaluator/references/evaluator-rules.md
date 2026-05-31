# Evaluator Rules

Rules and conventions for the skill-evaluator system.

## Pass/fail criteria

### Structural checks (behave)

A scenario passes when every `then` step assertion succeeds without raising `AssertionError`.
A scenario fails when any step raises `AssertionError` or an unexpected exception.

Structural checks must be **fully deterministic**: given the same artifact, the same scenario
always produces the same result. No LLM calls, no probabilistic assertions.

### LLM-as-judge checks

A rubric passes when:
- `JudgeVerdict.passed` is `True`.

A rubric fails when `JudgeVerdict.passed` is `False`.

The judge model is the Claude Code adapter's judge model.
The judge prompt must instruct the model to respond with JSON only:
`{"passed": <bool>, "score": <float 0.0-1.0>, "reasoning": <one sentence>}`

### Skill input size

The runner reports character counts for `SKILL.md` and `fixtures/input_*.md` as a proxy for input tokens. Use these counts with pass rates and judge scores to compare whether shorter instructions or prompts maintain output quality.

---

## Fixture conventions

### Golden fixtures (`fixtures/*.md`, `fixtures/*.js`, etc.)

- `valid_*.ext` — well-formed artifacts that should pass all structural checks.
- `invalid_*.ext` — intentionally broken artifacts that should fail at least one check.
  The failing scenario should assert the *presence* of the violation (not its absence).

### Input fixtures (`fixtures/input_*.md`)

Plain text prompts used in `invoke` mode. The runner passes the first `input_*.md` found
to the adapter. Name them descriptively: `input_crud_feature.md`, `input_timeseries.md`.

### Generated artifacts (`fixtures/_generated_artifacts/`)

Written by the runner during `invoke` mode — these are the files the agent produced.
Excluded by `environment.py` when `EVAL_ARTIFACTS_DIR` is not set (so golden fixture
scenarios never accidentally load generated output). The `_generated_artifacts/` directory
is gitignored.

Use `_generated_artifacts_primary_` as the `artifact_file` value in a rubric to target
the primary chart/visualization file the agent wrote.

---

## Adding evals for a new skill

1. Create `skills/<skill-name>/evals/` with:
   - `environment.py` — copy from an existing skill's evals; no changes needed
   - `*.feature` — one file per concern (structural, rule compliance, quality)
   - `steps/structural_steps.py` — deterministic step definitions
   - `steps/quality_steps.py` — judge step definitions (copy template)
   - `fixtures/valid_*.ext` — at least one passing golden fixture
   - `fixtures/invalid_*.ext` — at least one negative fixture per anti-pattern
   - `rubrics/*.yaml` — one YAML per quality dimension (optional; required for `@judge` features)

2. Tag feature files:
   - `@<skill_name>` — always present, used to run a single skill's evals
   - `@judge` — present on quality.feature; causes scenarios to be skipped in structural mode

3. Run `uv run python -m runner.run --skill <name> --mode invoke` to verify.

---

## Rubric YAML format

```yaml
rubrics:
  - id: <snake_case_id>              # unique within the skill
    artifact_file: <filename>        # relative to evals/fixtures/
    artifact_section: <heading>      # optional; extract this ## section before judging
    prompt: |
      <instruction to the judge>
      Respond with JSON: {"passed": <bool>, "score": <float>, "reasoning": <one sentence>}
```

Rules:
- Every rubric must trace to a rule in the skill's own reference files.
- Do not add rubrics for qualities that can be checked deterministically.

---

## Running the evaluator

```bash
# From skills/skill-evaluator/runner/
uv run python -m runner.run --skill plan-it --mode invoke
uv run python -m runner.run --skill dataviz --mode all
uv run python -m runner.run --mode invoke   # all skills
```

Exit code: `0` = all checks passed, `1` = at least one check failed.

Reports are written to `skills/<skill-name>/evals/reports/<skill-name>-<YYYY-MM-DDTHH-MM-SS-ffffff>.md`.
