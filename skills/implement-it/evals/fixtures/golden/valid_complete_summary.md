---
id: "003"
issue: "TASK-003"
created: "2024-03-12"
updated: "2024-03-12"
---

# Implementation Summary: Add AgeValidator Value Object

## Related Task

[TASK-003](tasks/003-add-age-validator.md) — Add `AgeValidator` value object to enforce registration age constraints before any downstream service is called.

## Files Changed

- `src/validators/age_validator.py` — New: `AgeValidator` value object; raises `ValueError("age 15 is below minimum 18")` for out-of-range integers; raises `TypeError("age must be int, got str")` for non-integer input; stores valid age as `.value`
- `tests/unit/validators/test_age_validator.py` — New: 11 unit tests covering lower boundary (17 → fail, 18 → pass), upper boundary (120 → pass, 121 → fail), mid-range (30 → pass), type rejection (str, float, None, list), error message content assertions

## Behavior Implemented

`AgeValidator(age)` validates the integer at construction time. Ages below 18 raise `ValueError` with message `"age {value} is below minimum 18"`. Ages above 120 raise `ValueError` with `"age {value} exceeds maximum 120"`. Non-integer inputs raise `TypeError` with the actual type name. A valid age (18–120 inclusive) is stored as `self.value: int`. No mutable state; no setters.

## Design Notes

Implemented as a Value Object per OOP calisthenics: validation happens in `__init__`, the object is immutable after construction, and equality is by value (`__eq__` compares `.value`). No dependency injection needed — the validator has no external I/O. Chose `ValueError` over a custom exception because the domain error is a constraint violation on a primitive, not a domain event. A custom exception would be over-engineering for a single-field validator.

## Tests Added or Updated

- **Unit** (`test_age_validator.py`): boundary conditions (17, 18, 120, 121), mid-range (30), type rejection (str, float, None, list), error message format assertions for both ValueError and TypeError. 11 tests total. All use `pytest.raises` with `match=` to assert message content.
- No other test categories applicable — see below.

## Test Categories Not Applicable

- **Integration**: `AgeValidator` has no external I/O; unit tests cover the full observable behaviour.
- **E2E**: Single in-memory value object with no API or UI boundary.
- **Performance**: O(1) validation; no measurable throughput concern.
- **Security**: No network boundary, no user-supplied strings beyond the age integer itself.

## Validation Run

```
pytest tests/unit/validators/test_age_validator.py -v    11 passed in 0.04s
mypy src/validators/age_validator.py                      Success: no issues found
```

## Accessibility Notes

N/A — backend module with no UI.

## Observability Changes

N/A — validation errors surface as exceptions to the caller; no structured logging added (caller decides whether to log).

## ADR Updates

N/A — no existing ADRs affected. `AgeValidator` is a leaf module with no architectural implications.

## Unresolved Assumptions or Follow-Up

- Assumed 120 as the upper bound based on AC-2; task does not cite a medical or legal source. If the bound changes, only `AgeValidator.__init__` and its tests need updating.
