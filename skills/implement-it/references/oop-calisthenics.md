# OOP Object Calisthenics

Apply selectively — use when they remove duplication, enforce invariants, or prevent silent invalid states.
Code snippets use Python-style pseudocode readable in any OO language.

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

```
# Bad — constraint enforcement deferred to callers
def create_project(name: str, owner_id: str, max_members: int): ...
create_project("", "not-a-uuid", -1)  # invalid state, detected late

# Good — Value Objects validate at construction, fail at the boundary
class ProjectName:
    def __init__(self, value: str):
        value = value.strip() if value else ""
        if not value:
            raise ValueError(f"ProjectName cannot be blank; got {value!r}")
        if len(value) > 100:
            raise ValueError(f"ProjectName exceeds 100 chars; got len={len(value)}")
        self.value = value

    def __eq__(self, other) -> bool:
        return type(other) is type(self) and other.value == self.value

    def __hash__(self) -> int:
        return hash(self.value)
```

### Validation in Value Objects

All format and constraint checks belong in the Value Object constructor — not in services, controllers, or repositories.

```
class Email:
    def __init__(self, value: str):
        if not value or "@" not in value:
            raise ValueError(f"Email must contain @; got {value!r}")
        self.value = value

class Price:
    def __init__(self, amount: int, currency: str):
        if amount < 0:
            raise ValueError(f"Price amount must be >= 0; got {amount!r}")
        if not currency or len(currency) != 3:
            raise ValueError(f"Currency must be 3-letter ISO code; got {currency!r}")
        self.amount = amount
        self.currency = currency
```

### Validation in entities

Entities accept only pre-validated Value Objects — never raw primitives.

```
# Bad — entity re-validates raw strings; same rules duplicated in every caller
class Project:
    def __init__(self, name: str, owner_id: str):
        if not name or not name.strip():
            raise ValueError("name required")

# Good — entity is a composition of already-valid types; constructor adds no checks
class Project:
    def __init__(self, name: ProjectName, owner: UserId, price: Price):
        self.name = name
        self.owner = owner
        self.price = price
```

### First-class collections

When a collection of domain objects carries a rule (max size, uniqueness, non-empty), wrap it.

```
# Bad — enforcement scattered across callers
members: list[str] = []
if len(members) >= max_members:
    raise Exception("Too many members")

# Good — rule owned by the collection type
class MemberList:
    def __init__(self, members: list[UserId], capacity: MaxMembers):
        if len(members) > capacity.value:
            raise ValueError(
                f"MemberList exceeds capacity: {len(members)} > {capacity.value}"
            )
        self._members = list(members)

    def add(self, member: UserId) -> "MemberList":
        return MemberList([*self._members, member], self._capacity)
```

### Equality

Value Objects compare by value, not reference. Implement structural equality.

```
# Good
assert Email("user@example.com") == Email("user@example.com")  # True

# Bad — reference equality makes equal-value objects always unequal
a = Email("user@example.com")
b = Email("user@example.com")
a == b  # False — different objects, wrong result
```

## Law of Demeter — One Dot per Line

Call methods only on: itself, objects it created, objects passed as parameters, or objects it directly owns. Each extra dot couples the caller to internals it shouldn't see.

```
# Bad — caller walks through three objects
order.customer().address().city()

# Good — ask the nearest neighbor
order.shipping_city()
```

Exception: fluent interfaces (query builders, test assertion chains) chain by design and are not violations.

## Small Classes

A class that exceeds one screen is doing too much. Look for a second responsibility hiding inside it.

Good: `ProjectName` validates name rules. `CreateProjectService` orchestrates one use case.

Bad: One class validates input, sends email, writes to the database, formats responses, and checks permissions.

## Two Instance Variables or Fewer

Many instance variables signal multiple responsibilities. Use as a design signal, not a hard limit — if three variables clearly belong together and splitting would produce meaningless wrappers, keep them.

```
# Bad — four variables across two unrelated concerns
class Order:
    customer_name: str
    customer_email: str
    amount: int
    currency: str

# Good — composed of focused types
class Order:
    customer: Customer
    price: Price
```

## Tell, Don't Ask — No Getters or Setters

Don't pull data out of an object to act on it externally. Tell the object to do the work itself.

```
# Bad — caller extracts state, decides, pushes result back
if order.get_total() > 1000:
    order.set_discount(0.1)

# Good — object applies its own rule
order.apply_loyalty_discount()
```

Exception: read models, DTOs, and serialization boundaries exist to carry data outward — accessors there are expected.

## Method Shape

### One level of indentation per method

Each method body should have at most one level of indentation. Deeper nesting signals a need for guard clauses or extraction.

```
# Bad — two levels of nesting inside the method body
def process(order):
    if order.is_valid():
        if order.has_stock():
            charge(order)

# Good — guard clauses flatten the path
def process(order):
    if not order.is_valid():
        return
    if not order.has_stock():
        return
    charge(order)
```

### Never use else

`else` is always replaceable with an early return or a guard clause. Eliminating `else` forces the happy path to the left margin and makes error paths explicit.

```
# Bad
def get_discount(user):
    if user.is_premium():
        return 0.2
    else:
        return 0.0

# Good — early return, no else needed
def get_discount(user):
    if user.is_premium():
        return 0.2
    return 0.0
```
