# Evaluating Skill Quality

Use this reference when creating eval cases, expected outputs, assertions, grading rules, baseline comparisons, benchmark reports, or iteration loops.

Do not use this file for activation-only testing. For trigger precision, false positives, and false negatives in the `description` field, read `references/optimizing-descriptions.md`.

Do not use this file for strict field constraints. For required structure, frontmatter rules, naming rules, and validation requirements, read `references/specification.md`.

## Core principle

A skill is useful only if it improves agent output compared with a baseline.

Evaluate skills by comparing:

- output quality;
- correctness;
- completeness;
- repeatability;
- time cost;
- token cost;
- failure behavior;
- user-facing usefulness.

Always ask:

```text
Does the skill produce better results than no skill or the previous version?
```

## What to evaluate

Evaluate three layers:

1. **Activation quality**: whether the skill triggers for the right tasks.
2. **Output quality**: whether the result satisfies the task.
3. **Execution quality**: whether the agent follows the intended workflow efficiently and safely.

This file focuses on output and execution quality.

For activation quality, use `references/optimizing-descriptions.md`.

## Recommended eval directory

Use this shape:

```text
evals/
├── evals.json                  # Main output-quality eval cases
├── trigger-evals.json          # Optional activation evals
├── files/                      # Optional input fixtures
├── assertions/                 # Optional reusable assertion specs
└── results/                    # Optional generated results
```

For full benchmark runs, write results outside the skill or inside an ignored workspace:

```text
skill-name-workspace/
└── iteration-1/
    ├── eval-case-id/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   └── grading.json
    │   └── baseline/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json
```

Use `baseline/` for either:

- no skill;
- the previous skill version;
- a competing skill version.

## `evals/evals.json` shape

Each eval case should include:

- `id`: stable identifier;
- `prompt`: realistic user task;
- `expected_output`: human-readable success description;
- `files`: optional input files;
- `assertions`: objective checks;
- `tags`: optional categories for analysis.

Example:

```json
{
  "skill_name": "skill-builder",
  "evals": [
    {
      "id": "create-minimal-skill",
      "prompt": "Create a minimal Agent Skill for validating JSON files.",
      "expected_output": "A valid skill directory with SKILL.md, a precise activation description, a clear workflow, and validation instructions.",
      "files": [],
      "tags": ["creation", "minimal"],
      "assertions": [
        "The output includes a skill directory name using lowercase letters and hyphens",
        "The output includes a valid SKILL.md frontmatter block",
        "The description says what the skill does and when to use it",
        "The body includes a clear workflow",
        "The output includes at least one validation step"
      ]
    },
    {
      "id": "fix-overbroad-description",
      "prompt": "This skill description triggers too often: `Use this skill for docs, prompts, workflows, and agents.` Improve it for a skill-builder skill.",
      "expected_output": "A narrower activation-oriented description that targets Agent Skill creation and maintenance without triggering on generic docs or prompts.",
      "files": [],
      "tags": ["description", "false-positive"],
      "assertions": [
        "The improved description starts with activation-oriented phrasing",
        "The improved description mentions Agent Skills or skill files",
        "The improved description includes concrete artifacts such as SKILL.md, scripts, references, assets, or evals",
        "The improved description avoids broad generic scope like all docs, prompts, workflows, and agents",
        "The improved description is under 1024 characters"
      ]
    }
  ]
}
```

## Designing good eval prompts

Good prompts are realistic, varied, and specific.

Include:

- real user phrasing;
- casual and formal wording;
- short prompts;
- detailed prompts;
- file paths;
- partial or flawed input;
- constraints;
- edge cases;
- ambiguous-but-solvable tasks.

Weak:

```text
Create a good skill.
```

Better:

```text
Create an Agent Skill for reviewing Python API error handling. Include SKILL.md, a references file for edge cases, and a validator command if needed.
```

Weak:

```text
Improve this.
```

Better:

```text
This SKILL.md has a vague description and no validation loop. Rewrite it so the agent knows when to activate it and how to verify the result.
```

## Eval coverage

Cover the important behavior categories.

For a skill-builder skill, include evals for:

- creating a new skill from scratch;
- validating an existing skill;
- fixing invalid frontmatter;
- improving weak descriptions;
- reducing false positives;
- adding support-file references;
- adding scripts;
- adding evals;
- refactoring an overlong `SKILL.md`;
- checking progressive disclosure;
- reviewing final quality.

Minimum starting set:

```text
3-5 evals
```

Stronger set:

```text
10-20 evals
```

Use tags to analyze categories:

```json
"tags": ["validation", "frontmatter", "negative-case"]
```

## Assertions

Assertions are concrete checks against the output.

Good assertions are:

- observable;
- specific;
- relevant;
- not overly brittle;
- verifiable by a human, LLM judge, or script.

Good:

```text
The output includes a valid YAML frontmatter block with name and description.
```

Good:

```text
The workflow includes a validation step that runs the bundled validator.
```

Weak:

```text
The output is good.
```

Too brittle:

```text
The output must contain the exact sentence "This skill validates JSON."
```

Prefer semantic assertions unless exact text is required.

## Assertion types

Use a mix of assertion types.

### Structural assertions

Check required files, sections, or fields.

```text
SKILL.md exists.
The frontmatter includes name and description.
The support files section references files by relative path.
```

### Behavioral assertions

Check the workflow or task behavior.

```text
The workflow tells the agent to inspect the current skill before editing.
The skill includes a validation loop before final output.
```

### Boundary assertions

Check that the output avoids unwanted behavior.

```text
The description does not trigger for generic Markdown editing.
The workflow does not load all references unconditionally.
```

### Quality assertions

Check usefulness and clarity.

```text
The description is specific enough to distinguish skill-building from generic prompt engineering.
The output explains remaining warnings clearly.
```

### Mechanical assertions

Check facts with scripts.

```text
The generated SKILL.md parses as valid YAML frontmatter.
The skill name matches the directory name.
All referenced files exist.
```

Mechanical assertions should be checked with scripts when possible.

## Grading

Grade each assertion as pass or fail.

Every grade must include evidence.

Use this shape:

```json
{
  "assertion_results": [
    {
      "text": "The output includes a valid YAML frontmatter block with name and description.",
      "passed": true,
      "evidence": "The generated SKILL.md starts with YAML frontmatter containing `name: json-validator` and a non-empty `description`."
    },
    {
      "text": "The workflow includes a validation step.",
      "passed": false,
      "evidence": "The output has Purpose and Workflow sections, but no validation command or review checklist."
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.5
  }
}
```

Rules:

- Require concrete evidence for a pass.
- Do not pass vague or implied behavior.
- Mark partial compliance as fail unless the assertion explicitly allows partial credit.
- Quote or reference output content when possible.
- Fix bad assertions in the next iteration.

## Baselines

Always compare against a baseline when practical.

Use one of:

```text
without_skill/   # agent runs without the skill
old_skill/       # previous version of this skill
baseline/        # generic name for either comparison
```

Use `without_skill/` when proving that the skill adds value over the agent alone.

Use `old_skill/` when improving an existing skill.

Compare:

- pass rate;
- critical failures;
- consistency;
- output usability;
- time;
- tokens;
- number of corrective turns needed.

## Running evals

For each eval case:

1. Start from a clean context.
2. Run the prompt with the skill.
3. Save outputs to `with_skill/outputs/`.
4. Run the same prompt against the baseline.
5. Save outputs to `baseline/outputs/`.
6. Grade both outputs using the same assertions.
7. Record timing and token data when available.
8. Aggregate results into `benchmark.json`.

Example task instruction for a with-skill run:

```text
Execute this eval:

Skill path: /path/to/skill-builder
Prompt: Create a minimal Agent Skill for validating JSON files.
Input files: none
Save outputs to: skill-builder-workspace/iteration-1/create-minimal-skill/with_skill/outputs/
```

Example task instruction for a baseline run:

```text
Execute this eval without using the skill-builder skill:

Prompt: Create a minimal Agent Skill for validating JSON files.
Input files: none
Save outputs to: skill-builder-workspace/iteration-1/create-minimal-skill/baseline/outputs/
```

## Timing data

When possible, save timing and token data.

Shape:

```json
{
  "total_tokens": 3840,
  "duration_ms": 31200
}
```

Do not treat speed as more important than correctness.

A skill that adds some time but prevents critical failures is usually worthwhile.

A skill that doubles token use for no output improvement should be simplified.

## Benchmark report

Aggregate each iteration into `benchmark.json`.

Example:

```json
{
  "iteration": 1,
  "skill_name": "skill-builder",
  "run_summary": {
    "with_skill": {
      "pass_rate": {
        "mean": 0.86
      },
      "time_seconds": {
        "mean": 42.1
      },
      "tokens": {
        "mean": 4100
      }
    },
    "baseline": {
      "pass_rate": {
        "mean": 0.52
      },
      "time_seconds": {
        "mean": 30.4
      },
      "tokens": {
        "mean": 2600
      }
    },
    "delta": {
      "pass_rate": 0.34,
      "time_seconds": 11.7,
      "tokens": 1500
    }
  },
  "notable_failures": [
    {
      "eval_id": "fix-overbroad-description",
      "configuration": "with_skill",
      "summary": "The output improved the description but did not include near-miss boundaries."
    }
  ]
}
```

## Interpreting results

Look for patterns, not only totals.

### Skill adds clear value

Signs:

- with-skill pass rate is meaningfully higher;
- fewer critical failures;
- outputs are more complete;
- workflow is more consistent;
- validation is more reliable.

Action:

```text
Keep the useful instructions and consider trimming anything that did not affect outcomes.
```

### Skill adds little value

Signs:

- with-skill and baseline outputs are similar;
- assertions pass without the skill;
- token cost increases with little quality gain.

Action:

```text
Remove generic instructions. Add only domain-specific guidance, scripts, or gotchas the baseline missed.
```

### Skill is too heavy

Signs:

- output improves slightly but token/time cost grows too much;
- agent follows irrelevant sections;
- outputs become verbose or overconstrained.

Action:

```text
Move rare details to references. Keep only core workflow and critical gotchas in SKILL.md.
```

### Skill is inconsistent

Signs:

- same eval passes in one run and fails in another;
- high variance across runs;
- agent interprets workflow differently each time.

Action:

```text
Make instructions more concrete. Add examples, defaults, and validation gates.
```

### Assertions are weak

Signs:

- both skill and baseline always pass;
- assertion does not distinguish quality;
- assertion is too vague;
- assertion checks formatting but not correctness.

Action:

```text
Replace with stricter observable assertions.
```

## Improvement loop

Use this loop for every meaningful skill change:

1. Run evals against the current skill and baseline.
2. Grade outputs with evidence.
3. Identify repeated failures.
4. Update only the instructions, scripts, assets, or references that address those failures.
5. Run the validator.
6. Re-run the evals.
7. Compare benchmark deltas.
8. Keep improvements that increase quality more than they increase complexity.
9. Remove instructions that do not improve eval outcomes.

Do not rewrite the whole skill after every failure.

Prefer targeted changes.

## Blind comparison

Use blind comparison when both outputs pass the same assertions but one may be more useful.

Prompt for blind review:

```text
Compare Output A and Output B without knowing which used the skill.

Score each from 1-5 on:
- correctness;
- completeness;
- clarity;
- usability;
- concision;
- adherence to requested format.

Then choose the better output and explain with evidence.
```

Save results as:

```text
blind-comparison.json
```

Shape:

```json
{
  "eval_id": "create-minimal-skill",
  "scores": {
    "output_a": {
      "correctness": 4,
      "completeness": 5,
      "clarity": 4,
      "usability": 5,
      "concision": 4
    },
    "output_b": {
      "correctness": 3,
      "completeness": 3,
      "clarity": 4,
      "usability": 3,
      "concision": 5
    }
  },
  "winner": "output_a",
  "evidence": "Output A included validation commands and explicit support-file load conditions; Output B did not."
}
```

## Mechanical grading scripts

Use scripts for checks that can be objectively verified.

Examples:

```bash
test -f SKILL.md
```

```bash
uv run scripts/validate_skill.py --skill-dir .
```

```bash
python - <<'PY'
from pathlib import Path
text = Path("SKILL.md").read_text()
assert "## Workflow" in text
assert "## Validation" in text
PY
```

For repeated grading, create a script:

```text
scripts/grade_skill_output.py
```

Expected interface:

```bash
uv run scripts/grade_skill_output.py \
  --outputs skill-builder-workspace/iteration-1/create-minimal-skill/with_skill/outputs \
  --assertions evals/assertions/create-minimal-skill.json \
  --format json
```

Python grading scripts should:

- use `argparse`;
- use PEP 723 inline dependencies if needed;
- print JSON to stdout with `--format json`;
- exit non-zero on invalid inputs or failed mechanical checks when appropriate.

## Eval case quality checklist

Before adding an eval case, verify:

- [ ] The prompt is realistic.
- [ ] The expected output is specific.
- [ ] The eval tests an important skill behavior.
- [ ] The eval is not just testing generic agent ability.
- [ ] Assertions are observable.
- [ ] Assertions are not overly brittle.
- [ ] At least one assertion checks correctness or usefulness.
- [ ] Input files are included when needed.
- [ ] The eval can be compared against a baseline.
- [ ] The eval has tags for later analysis.

## Assertion quality checklist

Before accepting assertions, verify:

- [ ] Each assertion can be graded as pass/fail.
- [ ] Each assertion has clear evidence requirements.
- [ ] Assertions cover structure, behavior, and quality.
- [ ] Assertions are not all superficial formatting checks.
- [ ] Assertions are not exact-text checks unless exact text matters.
- [ ] Assertions distinguish with-skill quality from baseline quality.
- [ ] Mechanical checks are handled by scripts when possible.

## Benchmark acceptance checklist

Before accepting a skill improvement, verify:

- [ ] With-skill pass rate improved or critical failures decreased.
- [ ] The improvement is visible in specific assertions.
- [ ] Token and time costs are acceptable.
- [ ] Failures were analyzed by category.
- [ ] Weak assertions were removed or improved.
- [ ] Instructions that did not help were trimmed.
- [ ] New failures were not introduced.
- [ ] The final skill passes structural validation.
- [ ] Remaining warnings are documented.

## Common failure modes

### Eval prompts are too generic

Weak:

```text
Make a skill.
```

Fix:

```text
Create an Agent Skill for reviewing SQL migration safety. Include SKILL.md, a validation workflow, and support-file references if needed.
```

### Assertions only check formatting

Weak:

```text
The output has Markdown headings.
```

Fix:

```text
The output includes a workflow that validates frontmatter, support-file references, and script usability.
```

### No baseline

Problem:

```text
The skill output looks good, but there is no comparison.
```

Fix:

```text
Run the same eval without the skill or against the previous skill version.
```

### Overfitting to evals

Problem:

```text
The skill contains exact phrases from eval prompts but fails similar tasks.
```

Fix:

```text
Generalize the instruction. Add validation-set prompts with different wording.
```

### Too many evals too early

Problem:

```text
Large eval suite before the skill shape is stable.
```

Fix:

```text
Start with 3-5 high-value evals. Expand after the first improvement loop.
```

## Output format for eval reviews

When reviewing eval results, return:

```text
Summary:
- <overall result>

Benchmark:
- With skill: <pass rate>
- Baseline: <pass rate>
- Delta: <difference>

Key wins:
- <where the skill helped>

Failures:
- <eval id>: <failure and evidence>

Recommended changes:
1. <targeted change>
2. <targeted change>

Next evals to add:
- <eval idea>
```

## Final rule

Do not treat evals as bureaucracy.

Use evals to answer one practical question:

```text
What specific instruction, script, reference, or asset made the agent better, and is it worth the added complexity?
```