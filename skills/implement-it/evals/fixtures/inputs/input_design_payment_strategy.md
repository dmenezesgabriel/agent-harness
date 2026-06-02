# Task: Implement Payment Processing with Multiple Methods

## Summary

Add payment processing supporting three methods: credit card, PayPal, and wire transfer. The `CheckoutService.process(type, amount)` currently uses a long `if/switch` chain to select the payment method. We need to clean this up so adding a fourth method (e.g., crypto) does not require changing existing code.

## Acceptance Criteria

- AC-1: Each payment method is implemented in its own class
- AC-2: `CheckoutService.process(type, amount)` selects the correct implementation without an if/switch chain
- AC-3: Adding a new payment method does not change any existing payment class
- AC-4: An invalid type raises `ValueError` with a message containing the unknown type
- AC-5: All unit tests pass with `pytest tests/unit/`

## File Locations

- Implementation: `src/payments/`
- Tests: `tests/unit/payments/`

## Non-Functional Requirements

- NFR-1: Each payment method class must be testable in isolation
- NFR-2: No framework-specific annotations or base classes

## Out of Scope

- Refund logic, partial captures, or recurring billing
- PCI compliance, tokenisation, or payment gateway SDK wrappers
- User interface or checkout page
