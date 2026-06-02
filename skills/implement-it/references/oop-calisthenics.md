# OOP Object Calisthenics

Apply selectively — use when they remove duplication, enforce invariants, or prevent silent invalid states.
Code snippets use TypeScript-style pseudocode (public, private, protected, constructor) readable in any OO language.

## Primitive Obsession and Value Objects

Replace raw primitives with typed Value Objects when a primitive carries a domain rule, format constraint, or role-specific identity. A Value Object is immutable, self-validating at construction, and equality-based.

### When to wrap

Wrap when:
- A primitive has a constraint: email must contain @, price must be ≥ 0, name must be non-blank
- A primitive has a format rule: ISO date, UUID, postal code, phone number
- Two primitives share the same type but different domain roles, enabling silent swaps
- The same constraint appears in multiple callers

Don't wrap when:
- No constraint exists beyond the primitive's own type
- The codebase consistently uses raw primitives and refactoring is out of task scope

### Value Object construction

```typescript
// Bad — constraint enforcement deferred to callers
function createProject(name: string, ownerId: string, maxMembers: number): void { ... }
createProject("", "not-a-uuid", -1)  // invalid state, detected late

// Good — Value Objects validate at construction, fail at the boundary
class ProjectName {
  readonly value: string

  constructor(raw: string) {
    const trimmed = raw.trim()
    if (!trimmed) {
      throw new Error(`ProjectName cannot be blank; got ${raw}`)
    }
    if (trimmed.length > 100) {
      throw new Error(`ProjectName exceeds 100 chars; got len=${trimmed.length}`)
    }
    this.value = trimmed
  }

  equals(other: unknown): boolean {
    return other instanceof ProjectName && other.value === this.value
  }
}
```

### Validation in Value Objects

All format and constraint checks belong in the Value Object constructor — not in services, controllers, or repositories.

```typescript
class Email {
  readonly value: string

  constructor(value: string) {
    if (!value || !value.includes("@")) {
      throw new Error(`Email must contain @; got ${value}`)
    }
    this.value = value
  }
}

class Price {
  readonly amount: number
  readonly currency: string

  constructor(amount: number, currency: string) {
    if (amount < 0) {
      throw new Error(`Price amount must be >= 0; got ${amount}`)
    }
    if (!currency || currency.length !== 3) {
      throw new Error(`Currency must be 3-letter ISO code; got ${currency}`)
    }
    this.amount = amount
    this.currency = currency
  }
}
```

### Validation in entities

Entities accept only pre-validated Value Objects — never raw primitives.

```typescript
// Bad — entity re-validates raw strings; same rules duplicated in every caller
class Project {
  constructor(name: string, ownerId: string) {
    if (!name || !name.trim()) {
      throw new Error("name required")
    }
  }
}

// Good — entity is a composition of already-valid types; constructor adds no checks
class Project {
  constructor(
    readonly name: ProjectName,
    readonly owner: UserId,
    readonly price: Price
  ) {}
}
```

### First-class collections

When a collection of domain objects carries a rule (max size, uniqueness, non-empty), wrap it.

```typescript
// Bad — enforcement scattered across callers
const members: string[] = []
if (members.length >= maxMembers) {
  throw new Error("Too many members")
}

// Good — rule owned by the collection type
class MemberList {
  private readonly members: readonly UserId[]

  constructor(members: readonly UserId[], private capacity: MaxMembers) {
    if (members.length > capacity.value) {
      throw new Error(
        `MemberList exceeds capacity: ${members.length} > ${capacity.value}`
      )
    }
    this.members = [...members]
  }

  add(member: UserId): MemberList {
    return new MemberList([...this.members, member], this.capacity)
  }
}
```

### Equality

Value Objects compare by value, not reference. Implement structural equality.

```typescript
// Good — structural equality
new Email("user@example.com").equals(new Email("user@example.com"))  // True

// Bad — reference equality makes equal-value objects always unequal
const a = new Email("user@example.com")
const b = new Email("user@example.com")
a === b  // False — different objects, wrong result
```

## Law of Demeter — One Dot per Line

Call methods only on: itself, objects it created, objects passed as parameters, or objects it directly owns. Each extra dot couples the caller to internals it shouldn't see.

```typescript
// Bad — caller walks through three objects
order.customer().address().city()

// Good — ask the nearest neighbor
order.shipping_city()
```

Exception: fluent interfaces (query builders, test assertion chains) chain by design and are not violations.

## Small Classes

A class that exceeds one screen is doing too much. Look for a second responsibility hiding inside it.

Good: `ProjectName` validates name rules. `CreateProjectService` orchestrates one use case.

Bad: One class validates input, sends email, writes to the database, formats responses, and checks permissions.

## Two Instance Variables or Fewer

Many instance variables signal multiple responsibilities. Use as a design signal, not a hard limit — if three variables clearly belong together and splitting would produce meaningless wrappers, keep them.

```typescript
// Bad — four variables across two unrelated concerns
class Order {
  customerName: string
  customerEmail: string
  amount: number
  currency: string
}

// Good — composed of focused types
class Order {
  customer: Customer
  price: Price
}
```

## Tell, Don't Ask — No Getters or Setters

Don't pull data out of an object to act on it externally. Tell the object to do the work itself.

```typescript
// Bad — caller extracts state, decides, pushes result back
if (order.getTotal() > 1000) {
  order.setDiscount(0.1)
}

// Good — object applies its own rule
order.applyLoyaltyDiscount()
```

Exception: read models, DTOs, and serialization boundaries exist to carry data outward — accessors there are expected.

## Method Shape

### One level of indentation per method

Each method body should have at most one level of indentation. Deeper nesting signals a need for guard clauses or extraction.

```typescript
// Bad — two levels of nesting inside the method body
function process(order: Order): void {
  if (order.isValid()) {
    if (order.hasStock()) {
      charge(order)
    }
  }
}

// Good — guard clauses flatten the path
function process(order: Order): void {
  if (!order.isValid()) return
  if (!order.hasStock()) return
  charge(order)
}
```

### Never use else

`else` is always replaceable with an early return or a guard clause. Eliminating `else` forces the happy path to the left margin and makes error paths explicit.

```typescript
// Bad
function getDiscount(user: User): number {
  if (user.isPremium()) {
    return 0.2
  } else {
    return 0.0
  }
}

// Good — early return, no else needed
function getDiscount(user: User): number {
  if (user.isPremium()) return 0.2
  return 0.0
}
```
