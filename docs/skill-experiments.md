# Skill Experiments Usage

This repo supports non-destructive skill experiments using `uv` inline-script dependencies, generated skill variants, eval manifests, and MLflow runs.

All scripts in `scripts/skill-evals/` are self-contained `uv run --script` files, so you do not need to manage a project virtualenv first.

## Files involved

### Baseline skill

- `skills/software-feature-planning/SKILL.md`

This is the source of truth and should not be overwritten during experiments.

### Eval inputs

- `skills/software-feature-planning/evals/evals.json`
- `skills/software-feature-planning/evals/variants.yaml`

### Scripts

- `scripts/skill-evals/generate_variants.py`
- `scripts/skill-evals/score_triggers.py`
- `scripts/skill-evals/score_outputs.py`
- `scripts/skill-evals/semantic_score.py`
- `scripts/skill-evals/semantic_split.py`
- `scripts/skill-evals/report.py`
- `scripts/skill-evals/run_skill_mlflow.py`

### Generated outputs

- `experiments/variants/software-feature-planning/<variant>/SKILL.md`
- `experiments/variants/software-feature-planning/<variant>/metadata.json`
- `mlruns/`

`experiments/variants/` and `mlruns/` are gitignored.

---

## 1. Generate skill variants

Render variants without mutating the baseline skill:

```bash
uv run scripts/skill-evals/generate_variants.py \
  --skill-dir skills/software-feature-planning
```

Render only one variant:

```bash
uv run scripts/skill-evals/generate_variants.py \
  --skill-dir skills/software-feature-planning \
  --variant concise-trigger
```

### Variant config format

`skills/software-feature-planning/evals/variants.yaml` currently looks like:

```yaml
variants:
  - id: baseline
    description: ...

  - id: concise-trigger
    description: ...
    body_prefix: |
      > Variant focus: ...

  - id: delivery-focused
    description: ...
    replacements:
      - old: "Prefer incremental vertical slices over broad foundational rewrites:"
        new: "Prefer incremental vertical slices over broad foundational rewrites, and prefer the smallest end-to-end slice that can be evaluated safely:"
```

### How variants are applied

Each variant can change:

- `description`
- `body_prefix`
- `body_suffix`
- `context` values for a custom Jinja template
- `replacements` for exact one-shot text substitutions

If no custom template is provided, the default renderer keeps the original `SKILL.md` body and lets you modify frontmatter and prepend/append variant-specific guidance.

---

## 2. Prepare eval run files

The manifest lives at:

- `skills/software-feature-planning/evals/evals.json`

It contains:

- trigger cases
- output cases
- expected intent labels
- expected entities
- assertion checks for output shape/content

### Trigger run file format

Create `runs/triggers.json` as JSON array or JSONL.

Example:

```json
[
  {
    "id": "trigger-train-01",
    "triggered": true,
    "predicted_intent": "feature_planning",
    "predicted_entities": [
      "scheduled invoice reminders",
      "acceptance criteria",
      "rollout slices"
    ]
  },
  {
    "id": "trigger-train-02",
    "triggered": false,
    "predicted_intent": "other",
    "predicted_entities": ["python function", "json"]
  }
]
```

Supported fields:

- `id` — required, must match manifest case id
- `triggered` — required boolean
- `predicted_intent` — optional intent prediction
- `predicted_entities` — optional list of extracted entities

### Output run file format

Create `runs/outputs.json` as a JSON object keyed by eval id.

Example:

```json
{
  "output-train-01": {
    "text": "### Feature Plan: ...",
    "files": []
  },
  "output-validation-01": {
    "text": "### Feature Plan: ...",
    "files": []
  }
}
```

Supported value formats:

- string:

```json
{
  "output-train-01": "plain text output"
}
```

- object:

```json
{
  "output-train-01": {
    "text": "plain text output",
    "files": ["artifact.png"]
  }
}
```

---

## 3. Score triggers only

Against the baseline skill:

```bash
uv run scripts/skill-evals/score_triggers.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --runs runs/triggers.json \
  --skill-dir skills/software-feature-planning
```

Against a generated variant:

```bash
uv run scripts/skill-evals/score_triggers.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --runs runs/triggers.json \
  --skill-dir experiments/variants/software-feature-planning/concise-trigger
```

### Trigger report includes

- `precision`
- `recall`
- `f1`
- `accuracy`
- `intent_accuracy` when intents are present
- `entity_precision`
- `entity_recall`
- `entity_f1`
- `false_positives`
- `false_negatives`
- `intent_mismatches`
- `entity_mismatches`
- `top_semantic_matches`

---

## 4. Run optional embedding-based semantic routing diagnostics

This uses a SentenceTransformer model to measure prompt-to-skill similarity, route positives against all skill descriptions, and optionally cluster failures.

```bash
uv run scripts/skill-evals/semantic_score.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --runs runs/triggers.json \
  --skill-dir skills/software-feature-planning \
  --skills-dir skills \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --top-k 3 \
  --cluster-failures
```

### Semantic report includes

- per-case `target_similarity`
- per-case `target_rank`
- `top_routes` across all skills
- `positive_route_top1_accuracy`
- `positive_route_top3_accuracy` or chosen top-k metric
- positive/negative similarity means
- positive/negative margin means
- `route_confusions`
- optional `failure_clusters`

Use this when you want to compare wording variants semantically, not only with fuzzy/TF-IDF heuristics.

Note: the first run may download the selected SentenceTransformer model.

---

## 5. Run optional embedding-aware semantic split generation

This creates train/validation splits that try to maximize semantic diversity within each bucket.

```bash
uv run scripts/skill-evals/semantic_split.py \
  --input skills/software-feature-planning/evals/evals.json \
  --output skills/software-feature-planning/evals/evals.semantic-split.json \
  --report skills/software-feature-planning/evals/evals.semantic-split.report.json \
  --model sentence-transformers/all-MiniLM-L6-v2
```

### Semantic split diagnostics include

- per-bucket train/validation counts
- nearest-neighbor similarity statistics
- cross-split near-duplicate leakage above the built-in threshold

Use this when random splitting is too noisy and you want validation prompts to cover a broader semantic surface.

Note: the first run may download the selected SentenceTransformer model.

---

## 6. Score outputs only

```bash
uv run scripts/skill-evals/score_outputs.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --outputs runs/outputs.json \
  --artifact-root skills/software-feature-planning/evals
```

### Output report includes

- per-case assertion results
- pass/fail evidence per assertion
- overall `pass_rate`

---

## 7. Aggregate reports manually

If you already have separate report files:

```bash
uv run scripts/skill-evals/report.py \
  --inputs trigger-report.json output-report.json
```

This produces a combined benchmark summary with aggregate pass/fail counts and metric mean/stddev.

---

## 8. Run the full MLflow workflow

### Baseline skill

```bash
uv run scripts/skill-evals/run_skill_mlflow.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --trigger-runs runs/triggers.json \
  --outputs runs/outputs.json \
  --skill-dir skills/software-feature-planning \
  --experiment-name software-feature-planning-evals \
  --run-name baseline
```

### Baseline skill with semantic routing diagnostics

```bash
uv run scripts/skill-evals/run_skill_mlflow.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --trigger-runs runs/triggers.json \
  --outputs runs/outputs.json \
  --skill-dir skills/software-feature-planning \
  --semantic-model sentence-transformers/all-MiniLM-L6-v2 \
  --skills-dir skills \
  --semantic-top-k 3 \
  --cluster-failures \
  --experiment-name software-feature-planning-evals \
  --run-name baseline-semantic
```

### Generated variant

When evaluating a generated variant, pass both:

- `--skill-dir` pointing to the generated variant directory
- `--variant` pointing to the generated variant `SKILL.md` for logging

```bash
uv run scripts/skill-evals/run_skill_mlflow.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --trigger-runs runs/triggers.json \
  --outputs runs/outputs.json \
  --skill-dir experiments/variants/software-feature-planning/concise-trigger \
  --variant experiments/variants/software-feature-planning/concise-trigger/SKILL.md \
  --experiment-name software-feature-planning-evals \
  --run-name concise-trigger
```

### What gets logged

#### Params

- skill name
- manifest path + hash
- skill dir
- variant path + hash
- trigger/output counts
- tracking URI

#### Metrics

- trigger precision / recall / f1 / accuracy
- intent accuracy
- entity precision / recall / f1
- output pass rate
- benchmark pass rate
- optional semantic routing metrics:
  - top-1 / top-k route accuracy on positives
  - target similarity means
  - route margin means

#### Artifacts

- manifest
- trigger runs
- output runs
- generated variant skill file
- split trigger/output manifests
- trigger/output reports
- benchmark summary

---

## 9. Open MLflow UI

```bash
uvx mlflow ui --backend-store-uri file:./mlruns
```

Then compare runs such as:

- `baseline`
- `concise-trigger`
- `delivery-focused`

A useful workflow is to keep the same `--experiment-name` and vary only:

- `--run-name`
- `--skill-dir`
- `--variant`
- input run files

---

## 10. Recommended experiment loop

1. Edit `skills/software-feature-planning/evals/variants.yaml`
2. Render variants with `generate_variants.py`
3. Produce trigger/output run files from the agent under test
4. Run `run_skill_mlflow.py` for each variant
5. Compare MLflow metrics and artifacts
6. Promote successful wording back into the baseline skill manually

This keeps experimentation safe: generated variants are disposable, while the baseline skill remains stable.

---

## 11. Notes and caveats

- `score_triggers.py` uses the `SKILL.md` in `--skill-dir` to read the current skill description.
- `--variant` in `run_skill_mlflow.py` is only for artifact logging; the actual trigger evaluation follows `--skill-dir`.
- Output evals score captured outputs, not the skill file itself, so you must generate `runs/outputs.json` from the variant being tested.
- Exact `replacements` in `variants.yaml` must match exactly once.

---

## 12. Minimal quickstart

```bash
uv run scripts/skill-evals/generate_variants.py \
  --skill-dir skills/software-feature-planning

uv run scripts/skill-evals/run_skill_mlflow.py \
  --manifest skills/software-feature-planning/evals/evals.json \
  --trigger-runs runs/triggers.json \
  --outputs runs/outputs.json \
  --skill-dir experiments/variants/software-feature-planning/baseline \
  --variant experiments/variants/software-feature-planning/baseline/SKILL.md \
  --experiment-name software-feature-planning-evals \
  --run-name baseline

uvx mlflow ui --backend-store-uri file:./mlruns
```
