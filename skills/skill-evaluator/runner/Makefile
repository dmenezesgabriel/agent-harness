.PHONY: check format lint type test coverage test-structure security arch deps dead-code complexity semgrep

PYTHON_TARGETS := runner ../../dataviz/evals
QUALITY_TARGETS := $(PYTHON_TARGETS) tests scripts

check: format lint type coverage test-structure deps dead-code complexity security arch semgrep

format:
	uv run ruff format --check $(QUALITY_TARGETS)

lint:
	uv run ruff check $(QUALITY_TARGETS)

type:
	uv run mypy

test:
	uv run pytest

coverage:
	uv run pytest --cov=runner --cov-fail-under=75

test-structure:
	uv run python scripts/check_test_module_parity.py

deps:
	uv run deptry .

dead-code:
	uv run vulture $(QUALITY_TARGETS) --min-confidence 90

complexity:
	uv run radon cc $(QUALITY_TARGETS) -n C

security:
	uv run bandit -r $(QUALITY_TARGETS) -c pyproject.toml

arch:
	uv run lint-imports

semgrep:
	uv run semgrep scan --config .semgrep/python-quality.yml --error --quiet $(QUALITY_TARGETS)
