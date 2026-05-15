# Software Design Principles

## Purpose

Use this reference as a quick design check during implementation or refactoring. These principles help you place behavior, shape boundaries, and manage dependencies.

Treat them as heuristics, not laws. They guide judgment; they do not replace it.

## SOLID

### SRP — Single Responsibility Principle

**Definition:** A unit should have one reason to change.

**Practical signal:** If one function, module, or component is pulled in different directions by unrelated changes, responsibility is mixed.

**Common misuse / warning:** Do not split code into tiny pieces just to say each file has one job. Group behavior that changes together.

**Example:** Keep invoice total calculation separate from invoice email delivery so pricing-rule changes do not force edits to notification code.

### OCP — Open/Closed Principle

**Definition:** Prefer extending behavior over repeatedly modifying stable code paths.

**Practical signal:** A new variation can be added by plugging in new behavior at an existing seam instead of editing a large conditional used by many callers.

**Common misuse / warning:** Do not introduce abstractions for hypothetical future variation. Wait for a real change pressure.

**Example:** Add a new discount policy as a separate policy object or function selected by configuration, rather than expanding one central `if/else` chain for every new discount type.

### LSP — Liskov Substitution Principle

**Definition:** A replacement should preserve the contract callers rely on.

**Practical signal:** Callers can use either implementation through the same contract without special cases, surprise errors, or changed meaning.

**Common misuse / warning:** Matching method names is not enough. Inputs, outputs, errors, and side effects must still honor expectations.

**Example:** If a storage service promises `load(id)` returns missing/not-found in a defined way, every implementation should handle absent data the same way instead of one returning null and another throwing unexpectedly.

### ISP — Interface Segregation Principle

**Definition:** Clients should depend only on the operations they need.

**Practical signal:** Callers use a small, focused API instead of receiving a large surface where most members are irrelevant.

**Common misuse / warning:** Do not create many near-duplicate interfaces with no clear client need. Split interfaces around real usage patterns.

**Example:** A report generator that only reads records should depend on a `RecordReader` contract, not a combined read/write/admin interface.

### DIP — Dependency Inversion Principle

**Definition:** Stable policy should depend on abstractions or seams, not volatile details.

**Practical signal:** Business rules can be tested and changed without pulling in database, network, UI, or framework details.

**Common misuse / warning:** An abstraction is useful only if it protects policy from detail volatility or enables clear seams. Do not wrap everything by default.

**Example:** An order-approval rule depends on a payment-check contract, while a separate adapter talks to the payment provider.

## Related Heuristics

### Cohesion
Keep behavior that changes together together. If code must usually be edited as a set, it probably belongs in the same unit.

### Coupling
Keep dependencies few, explicit, and purposeful. High coupling shows up when small changes force edits across many unrelated places.

### Boundaries
Make seams and contracts clear. Pass stable data across boundaries and avoid leaking internal state or framework details into wider code.

### Invariants
Protect rules where they are owned. If an entity, workflow, or module requires something to always be true, enforce it at that boundary.

### Stable dependency direction
Dependencies should point toward more stable policy and away from volatile details. Details may depend on policy; policy should not depend on details.

## References

- Robert C. Martin, "Getting a SOLID start." https://blog.objectmentor.com/articles/2009/02/12/getting-a-solid-start
- Robert C. Martin, "The Principles of OOD." http://www.butunclebob.com/ArticleS.UncleBob.PrinciplesOfOod
- Robert C. Martin, *Agile Software Development, Principles, Patterns, and Practices*. Prentice Hall, 2002.
