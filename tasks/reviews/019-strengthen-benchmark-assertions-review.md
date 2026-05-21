---
id: "019"
reviewed: 2026-05-21
verdict: Fail
blocking: 2
non-blocking: 2
suggestions: 1
---

# Review: Strengthen behavioral assertions and establish champion baselines

## Overall Verdict: Fail

Two Blocking findings prevent mark-complete. Both are operational steps explicitly listed in the Definition of Done (champion baseline promotion) that were not executed. All code changes are correct and well-tested.

---

## Acceptance Criteria Evaluation

| AC | Description | Result | Notes |
|----|-------------|--------|-------|
| AC-001 | File with `FR-001:` passes FR scenario | **Pass** | Covered by `test_passes_when_regex_matches` |
| AC-002 | File without FR ID fails and names the file | **Pass** | Covered by `test_fails_with_filename_when_no_match` |
| AC-003 | File with `status: active` passes frontmatter scenario | **Pass** | Covered by `test_passes_for_active_status` |
| AC-004 | File with `status: draft` fails frontmatter scenario | **Pass** | Covered by `test_fails_for_draft_status` |
| AC-005 | New scenarios appear in `behave_scenarios` artifact after 5-trial run | **Fail** | Benchmark was not run; no MLflow artifacts exist |
| AC-006 | `bench-compare` shows `★ champion` after promotion | **Fail** | Depends on FR-009/FR-010; benchmark not run |

---

## Findings

### Blocking

**B-001 — FR-009, FR-010, AC-005, AC-006: Champion baselines not established**

The Definition of Done explicitly requires:
> "Benchmark ran against unmodified plan-it and implement-it skills (5 trials each)."
> "bench-promote executed for both skills; bench-compare confirms ★ champion for each."

Neither the benchmark run nor the `bench-promote` calls were executed. The implementation summary acknowledges this and defers it to manual execution, which is reasonable given that running a live model benchmark inside a code implementation is impractical. However, the DoD requirement is hard — these steps must be completed before the task can be marked done.

**Action required**: Run `uv run python run.py --skill plan-it --platform pi-agent --model openai-codex/gpt-5.4-mini --trials 5`, capture the `skill_content_hash`, and run `bench-promote` for both plan-it and implement-it. Then verify `bench-compare` shows `★ champion`.

---

**B-002 — Validation executed outside project-mandated toolchain**

The implementation summary records the test run as `python3 -m pytest ...` using a bare `pip install` of dependencies, not `uv run pytest`. This bypassed the project's lockfile, caused an OOM crash on initial run (heavy transitive deps like pyarrow, scipy, scikit-learn), and the corrected run also used system `pip`. Tests pass, but the validation cannot be certified as reproducible against the locked dependency set.

**Action required**: Validate with `uv run pytest benchmarks/tests/test_common_steps.py -v` from the repo root and record that invocation in the summary.

---

### Non-blocking

**NB-001 — IT-001 and IT-002 incorrectly classified as requiring MLflow**

The implementation summary states IT-001 and IT-002 are out of scope because they "require behave runner against fixture workspaces and a live MLflow backend." This is incorrect: IT-001 and IT-002 only require a temporary workspace directory and the behave CLI — no MLflow, no live model. Only IT-003 genuinely requires those. The step logic is covered by unit tests, so this does not block the code, but the integration test coverage gap is real and should be addressed in a follow-up.

**Recommendation**: Add `tests/test_behave_integration.py` or a `tests/fixtures/` directory with well-formed and malformed issue file fixtures, then invoke behave as a subprocess from pytest for IT-001 and IT-002.

---

**NB-002 — FR-006 regex uses alternation group; Gherkin passthrough untested**

The scenario step `has content matching "Covers (FR|AC|NFR|OBS)-\d{3}"` relies on behave passing the string `Covers (FR|AC|NFR|OBS)-\d{3}` verbatim to `step_content_matches_regex`, which then calls `re.compile()` on it. The unit tests test the step function directly (bypassing behave's string parsing), so the full Gherkin→step path for a regex containing `(` and `|` characters has not been exercised. In practice this works, but there is no test that runs the scenario through the behave runner to confirm the regex is not escaped or truncated during parsing.

**Recommendation**: Cover in IT-001 when that integration test is added (see NB-001).

---

### Suggestions

**S-001 — `step_frontmatter_key_value` could produce a clearer error for files with no frontmatter block**

Currently, a file with no `---` delimiters fails with the generic "Frontmatter key 'X' with value 'Y' missing in: [filename]" message. Adding a distinct branch for "no frontmatter found" vs "key not present" vs "key has wrong value" would make failures easier to diagnose in benchmark output.

---

## Required Tests Evaluation

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| UT-001 | `step_content_matches_regex`: pass, fail with filename, vacuous | **Present** | 4 tests in `TestStepContentMatchesRegex` |
| UT-002 | `step_frontmatter_key_value`: active, draft, absent, vacuous | **Present** | 5 tests in `TestStepFrontmatterKeyValue` |
| IT-001 | Plan-it scenarios pass against good fixture via behave | **Missing** | Incorrectly deferred; no MLflow needed |
| IT-002 | Plan-it FR scenario fails against bad fixture via behave | **Missing** | Incorrectly deferred; no MLflow needed |
| IT-003 | Champion baseline established end-to-end | **Deferred** | Legitimately requires live model + MLflow |

---

## NFR Compliance

| NFR | Description | Status |
|-----|-------------|--------|
| NFR-001 | Step style: behave decorators, error includes filenames and workspace path, vacuous pass | **Pass** — both steps include `context.ws` in error and `if not files: return` |
| NFR-002 | Scenarios grouped under `# ── Content quality ──` | **Pass** — both feature files use this header |
| NFR-003 | Frontmatter step uses `re.MULTILINE`, matches `key:\s*value` without exact whitespace | **Pass** — regex is `rf"^{re.escape(key)}:\s*{re.escape(value)}\s*$"` with `re.MULTILINE`; `test_tolerates_no_space_after_colon` confirms |

---

## OBS Requirements

| OBS | Description | Status |
|-----|-------------|--------|
| OBS-001 | Benchmark logs `behave_pass_rate`, `f1`, `quality_score`, `input_tokens` per trial | **Pre-existing** — not in scope of this change; infrastructure already present |
| OBS-002 | `bench-compare` displays champion hash after promotion | **Blocked** — depends on B-001 (benchmark not run) |

---

## ADR Compliance

No ADR dependencies listed in the issue. No ADR changes required. ✅

---

## Unresolved Assumptions

- Whether the existing `behave_evaluator.py` will pick up the four new plan-it scenarios and two new implement-it scenarios automatically on the next benchmark run (likely yes, since behave discovers scenarios by feature file glob, but not confirmed without running).
- Whether `skill_content_hash` is stable across environments (i.e., the hash computed on the Termux device matches what would be logged in an MLflow run) — relevant for FR-009/010 promotion.
