---
id: "019"
created: 2026-05-21
status: complete
---

# Implementation Summary: Strengthen behavioral assertions and establish champion baselines

## Files Changed

- `benchmarks/features/steps/common_steps.py` — added two new step definitions
- `benchmarks/features/plan-it.feature` — added four content-quality scenarios
- `benchmarks/features/implement-it.feature` — added two content-quality scenarios
- `benchmarks/tests/test_common_steps.py` — new unit test file (9 tests)

## Behavior Implemented

### New step definitions (FR-001, FR-002)

**`every file in "{pattern}" has content matching "{regex}"`**  
Searches each file matched by the glob for the compiled regex. Fails with a list of non-matching filenames. Passes vacuously when no files match the glob.

**`every file in "{pattern}" has frontmatter key "{key}" with value "{value}"`**  
Extracts the YAML frontmatter block (between `---` delimiters) and checks for `key:\s*value` using `re.MULTILINE`. Tolerates `status:active` (no space) and `status: active` (with space). Passes vacuously when no files match.

### New Gherkin scenarios — plan-it.feature (FR-003–FR-006)

Under `# ── Content quality ──`:
- Every issue file contains at least one properly formatted functional requirement (`FR-\d{3}:`)
- Every issue file acceptance criteria contain observable Gherkin language (`Given`, `When`, or `Then`)
- Every issue file has active status in frontmatter (`status: active`)
- Every issue file contains test IDs linked to requirement IDs (`Covers (FR|AC|NFR|OBS)-\d{3}`)

### New Gherkin scenarios — implement-it.feature (FR-007–FR-008)

Under `# ── Content quality ──`:
- Every summary has a non-empty Design Notes section
- Every summary documents ADR update status (`ADR Updates` or `Not applicable`)

## Tests Added

`benchmarks/tests/test_common_steps.py` — 9 unit tests (UT-001, UT-002):
- `TestStepContentMatchesRegex` (4 tests): pass on match, fail with filename on no-match, vacuous pass, reports only bad files
- `TestStepFrontmatterKeyValue` (5 tests): pass for `active`, fail for `draft`, fail when key absent, vacuous pass, tolerates no space after colon

`benchmarks/tests/test_behave_integration.py` — 2 integration tests (IT-001, IT-002):
- `test_good_fixture_all_scenarios_pass`: full `plan-it.feature` passes against a well-formed fixture (covers FR-003–FR-006, NB-002 Gherkin regex passthrough)
- `test_fr_scenario_fails_on_missing_fr_id`: FR scenario fails and names the bad file (covers AC-002)

## Validations Run

```
uv run --no-project --with pytest --with behave python -m pytest \
  tests/test_common_steps.py tests/test_behave_integration.py -v
```
→ 11 passed, 0 failed

## Intentional Non-Applicable Categories

- **FR-009 / FR-010 (champion baselines)**: require a live benchmark run against `openai-codex/gpt-5.4-mini` with 5 trials each, then `bench-promote`. These are operational steps to run manually after infrastructure is available.
- **IT-003**: requires live model and MLflow — correctly deferred.
- **Accessibility**: no UI touched.
- **ADRs**: no architectural decisions changed.

## Unresolved Assumptions / Manual Steps Required

Champion promotion (FR-009, FR-010, AC-005, AC-006) must be completed manually:

```bash
# From benchmarks/
uv run python run.py --skill plan-it --platform pi-agent \
  --model openai-codex/gpt-5.4-mini --trials 5

uv run python run.py --skill implement-it --platform pi-agent \
  --model openai-codex/gpt-5.4-mini --trials 5

# Capture skill_content_hash from MLflow output, then:
bench-promote --skill plan-it --content-hash <hash>
bench-promote --skill implement-it --content-hash <hash>

# Verify:
bench-compare --skill plan-it
bench-compare --skill implement-it
```
