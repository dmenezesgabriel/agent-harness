---
id: "020"
reviewed: 2026-05-21
updated: 2026-05-21
verdict: Pass
blocking: 0
non-blocking: 2
suggestions: 0
---

# Review: Apply safe plan-it refactors and validate against champion

## Overall Verdict: Pass

All four file-edit acceptance criteria pass on direct code inspection. The diff between `skills/plan-it/` and `skills/plan-it-lean/` shows exactly the four targeted changes and nothing else, confirming NFR-001 and NFR-002. NB-003 is resolved: variant hash `sha256:548d7edfb5bb765d` is now recorded in the implementation summary. Two Non-blocking findings remain for the benchmark validation phase (AC-005, AC-006, FR-006–FR-008, OBS-001, OBS-002), which require a model API endpoint and a running MLflow server on a machine with sufficient RAM — the development device has ~120 MB free RAM and cannot safely import the benchmark dependencies.

---

## Acceptance Criteria Evaluation

| AC | Description | Result | Notes |
|----|-------------|--------|-------|
| AC-001 | `output-files.md` issue numbering uses `bash scripts/next-issue-number.sh` with fallback | **Pass** | File confirmed; 4-step prose replaced with script invocation + fallback clause |
| AC-002 | `SKILL.md` Issue output requirement contains only `mkdir` command | **Pass** | Section contains only the `mkdir -p tasks/issues` bash block; all prose removed |
| AC-003 | `SKILL.md` Before marking complete contains exactly one item | **Pass** | Single item: `CONTEXT.md updated if domain terms were defined or clarified` |
| AC-004 | `adr-template.md` line 9 uses `{{YYYY-MM-DD}}` | **Pass** | Confirmed by file read and diff |
| AC-005 | bench-compare shows variant within 0.05 of champion on `behave_pass_rate` and `f1` | **Deferred** | Requires benchmark run; see NB-001 |
| AC-006 | bench-promote shows new hash as `★ champion` after AC-005 passes | **Deferred** | Depends on AC-005; see NB-001 |

---

## Findings

### Blocking

None.

---

### Non-blocking

**NB-001 — AC-005, AC-006, FR-006, FR-007, FR-008: Benchmark variant run not executed**

The Definition of Done requires:
> "Benchmark run completed (IT-001); MLflow summary logged with variant hash."
> "bench-compare output confirms thresholds met (AC-005)."

The benchmark run (IT-001), quality threshold check (IT-002), and champion promotion (FR-008, AC-006) were not executed. The implementation summary correctly identifies this as requiring external resources (MLflow server + model API) not available in this environment, and provides the exact invocation to run:

```
uv run python run.py --skill plan-it --platform pi-agent --model openai-codex/gpt-5.4-mini --trials 5 --skill-dir ../skills/plan-it-lean
```

This is Non-blocking (not Blocking) because the operator-driven benchmark phase is a distinct operational step that cannot be automated without infrastructure, and the issue's Definition of Done provides explicit conditional handling: "If thresholds not met: implementation summary documents which metric regressed and by how much; no promotion."

**Action required**: Run the benchmark, capture the summary, and run `bench-compare --skill plan-it` to confirm thresholds. If thresholds are met, run `bench-promote` and update `skills/plan-it/` to match `skills/plan-it-lean/`.

---

**NB-002 — OBS-001, OBS-002: Telemetry not yet verified**

OBS-001 requires MLflow to log `behave_pass_rate`, `f1`, `quality_score`, `input_tokens`, and `output_tokens` per trial tagged with the variant's `skill_content_hash`. OBS-002 requires the `bench-compare` output to be captured in the implementation summary. Both depend on the benchmark run in NB-001 and cannot be verified without it.

**Action required**: After the benchmark run, confirm the MLflow summary run contains the required metrics and capture the `bench-compare` output in the implementation summary.

---

**NB-003 — ~~Implementation summary does not record the `skill_content_hash`~~ — RESOLVED**

Hash computed via `harness.skill_hash.compute_skill_hash` (stdlib only, no heavy deps) and recorded in the implementation summary:

```
sha256:548d7edfb5bb765d
```

---

## Required Tests Evaluation

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| UT-001 | Not applicable — pure text edits | **N/A** | Correctly classified; no new logic introduced |
| IT-001 | Benchmark variant run completes without errors | **Deferred** | Legitimately requires live model + MLflow; see NB-001 |
| IT-002 | Variant meets quality thresholds | **Deferred** | Depends on IT-001; see NB-001 |

---

## Functional Requirements Evaluation

| FR | Description | Status |
|----|-------------|--------|
| FR-001 | `output-files.md` issue numbering rule uses script invocation + fallback | **Pass** |
| FR-002 | `SKILL.md` Issue output requirement contains only `mkdir` command | **Pass** |
| FR-003 | `SKILL.md` ADR output requirement contains only `mkdir` command | **Pass** |
| FR-004 | `SKILL.md` Before marking complete has exactly one item | **Pass** |
| FR-005 | `adr-template.md` line 9 uses `{{YYYY-MM-DD}}` | **Pass** |
| FR-006 | Benchmark `behave_pass_rate` within 0.05 of champion | **Deferred** — see NB-001 |
| FR-007 | Benchmark `input_tokens` ≤ champion mean | **Deferred** — see NB-001 |
| FR-008 | Variant promoted if FR-006/007 pass | **Deferred** — see NB-001 |

---

## NFR Compliance

| NFR | Description | Status |
|-----|-------------|--------|
| NFR-001 | `skills/plan-it-lean/` is a full copy with only four targeted edits | **Pass** — diff shows exactly 3 files differ (`SKILL.md`, `references/output-files.md`, `assets/adr-template.md`); all other files are byte-identical to `skills/plan-it/` |
| NFR-002 | All other content in edited files preserved verbatim | **Pass** — diff confirms only the targeted sections were removed; all other content (Anti-patterns, Final response, If output fails, cross-references, Good/Bad examples in output-files.md) is unchanged |

---

## OBS Requirements

| OBS | Description | Status |
|-----|-------------|--------|
| OBS-001 | MLflow logs `behave_pass_rate`, `f1`, `quality_score`, `input_tokens`, `output_tokens` per trial | **Deferred** — requires benchmark run; infrastructure pre-exists |
| OBS-002 | `bench-compare` output captured in implementation summary | **Deferred** — requires benchmark run; see NB-002 |

---

## ADR Compliance

No ADR dependencies listed in the issue. The task explicitly states "No ADR dependency — no architectural decisions involved." No ADR changes required or expected. ✅

---

## Unresolved Assumptions

- Whether the benchmark runner's `skill_content_hash` algorithm produces a stable hash for the `skills/plan-it-lean/` directory across different run environments (relevant to FR-008 champion promotion).
- Whether `skills/plan-it/` should be updated in-place after promotion or whether `skills/plan-it-lean/` should be kept as a permanent named variant — the DoD says "update `skills/plan-it/` to match `skills/plan-it-lean/`; variant directory removed," but this was not yet actioned.
