# Task: Implement AgeValidator Value Object

## Summary

Add an `AgeValidator` class that validates a user's age before registration. This is a new module with no dependencies on existing code.

## Acceptance Criteria

- AC-1: `AgeValidator(age)` raises `ValueError` with a message containing the offending value when `age` is below 18
- AC-2: `AgeValidator(age)` raises `ValueError` with a message containing the offending value when `age` is above 120
- AC-3: `AgeValidator(age)` raises `TypeError` when `age` is not an integer (e.g. str, float, None)
- AC-4: Valid ages (18 through 120 inclusive) are accessible via `.value` after construction
- AC-5: All unit tests pass with `pytest tests/unit/`

## File Locations

- Implementation: `src/validators/age_validator.py`
- Tests: `tests/unit/validators/test_age_validator.py`

## Non-Functional Requirements

- NFR-1: No external dependencies beyond Python stdlib
- NFR-2: Explicit type annotations on all public functions and return types

## Out of Scope

- Database persistence
- API endpoints or serialisation
- UI components
- Integration with the registration service (that comes in a later task)
