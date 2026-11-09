# Quality gate for the find-* skill scripts and evals tooling.
# Everything resolves from uv.lock (hash-verified wheels; see [tool.uv] guards).
UV = uv run --locked

.PHONY: sync test lint types security audit actions deadcode deps complexity shell check commit-check mutmut validate

sync:
	@uv sync --locked

test:
	@$(UV) pytest

lint:
	@$(UV) ruff check .

types:
	@$(UV) pyright

security:
	@$(UV) bandit -c pyproject.toml -r skills evals

audit:
	@$(UV) pip-audit

# GitHub Actions / dependabot config security audit.
actions:
	@$(UV) zizmor .github

deadcode:
	@$(UV) vulture

deps:
	@$(UV) deptry .

# Worst block today is C(14); the gate blocks D+ and keeps the average at A.
# radon reports only B+ blocks (agent-token-efficient); xenon enforces.
complexity:
	@$(UV) radon cc skills evals/triggers/run_triggers.py evals/triggers/run_outcomes.py evals/triggers/outcome_checks.py -a -n B
	@$(UV) xenon --max-absolute C --max-modules C --max-average A skills evals/triggers/run_triggers.py evals/triggers/run_outcomes.py evals/triggers/outcome_checks.py

shell:
	@$(UV) shellcheck scripts/*.sh .githooks/pre-commit

# Full gate; `audit` hits the network, so run deliberately rather than per-commit.
check: test lint types security deadcode deps complexity shell audit actions

# Fast deterministic subset wired into both pre-commit configs.
commit-check: test lint types security deadcode deps complexity shell actions

# Mutation testing is slow (~minutes per script) — run deliberately, not per-commit.
# Runs per-skill from each scripts/ dir (see setup.cfg for why cwd matters).
mutmut:
	@for d in skills/*/scripts; do \
		echo "== $$d"; \
		(cd "$$d" && uv run mutmut run && uv run mutmut results) || exit $$?; \
	done

validate:
	@scripts/validate-skills.sh
