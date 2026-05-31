from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = PROJECT_ROOT / "runner"
TESTS_DIR = PROJECT_ROOT / "tests"


def main() -> None:
    expected_tests = {_expected_test_path(path) for path in _source_modules()}
    actual_tests = set(TESTS_DIR.rglob("test_*.py"))
    missing_tests = sorted(
        path.relative_to(PROJECT_ROOT) for path in expected_tests - actual_tests
    )
    extra_tests = sorted(
        path.relative_to(PROJECT_ROOT) for path in actual_tests - expected_tests
    )
    if missing_tests or extra_tests:
        raise SystemExit(_format_error(missing_tests, extra_tests))


def _source_modules() -> list[Path]:
    return [path for path in RUNNER_DIR.rglob("*.py") if path.name != "__init__.py"]


def _expected_test_path(source_path: Path) -> Path:
    relative_path = source_path.relative_to(RUNNER_DIR)
    return TESTS_DIR / relative_path.parent / f"test_{relative_path.name}"


def _format_error(missing_tests: list[Path], extra_tests: list[Path]) -> str:
    return (
        "runner test/module parity failed; expected tests/<module_path>/test_<module>.py "
        f"for every runner module. missing={missing_tests!r}; extra={extra_tests!r}"
    )


if __name__ == "__main__":
    main()
