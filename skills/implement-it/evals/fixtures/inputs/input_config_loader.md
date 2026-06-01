# Task: Implement ConfigLoader

## Summary

Add a `ConfigLoader` class that parses simple INI-style `key=value` configuration files. This is a new module with no dependencies on existing code.

## Acceptance Criteria

- AC-1: `ConfigLoader.load(path)` parses a file where each non-blank, non-comment line is `key=value` and returns `dict[str, str]`
- AC-2: `ConfigLoader.load(path)` raises `FileNotFoundError` with the file path in the message when the file does not exist
- AC-3: `ConfigLoader.load(path)` raises `ValueError` with the malformed line content in the message when a line is not blank, not a comment (does not start with `#`), and contains no `=`
- AC-4: Lines starting with `#` are treated as comments and skipped
- AC-5: All unit tests pass with `pytest tests/unit/`

## File Locations

- Implementation: `src/config/config_loader.py`
- Tests: `tests/unit/config/test_config_loader.py`

## Non-Functional Requirements

- NFR-1: No external dependencies beyond Python stdlib
- NFR-2: Explicit type annotations on all public functions and return types

## Out of Scope

- Type coercion (all values stay as strings)
- Sections (`[section]` headers)
- Default values or fallback chains
- Environment variable interpolation
