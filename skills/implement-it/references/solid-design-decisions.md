# SOLID Design Decisions

Decision tree: when a design decision arises, walk the tree. Each principle maps to concrete patterns with TypeScript-style pseudocode. Load this reference only when a design signal is present.

---

## Decision tree

```
When a design decision arises:
  │
  ├── One class/module has multiple reasons to change?
  │   └── Single Responsibility Principle (SRP)
  │       ├── Split into focused classes — each has one job
  │       ├── Consider Facade pattern to simplify a complex subsystem
  │       └── See [design-patterns.md](design-patterns.md#facade)
  │
  ├── Existing code must be modified when new behavior is added?
  │   └── Open/Closed Principle (OCP)
  │       ├── Extract varying behavior behind an interface
  │       ├── Consider Strategy pattern for interchangeable algorithms,
  │       │   often paired with Simple Factory for strategy selection
  │       └── See [design-patterns.md](design-patterns.md#strategy)
  │
  ├── Subtypes fail when substituted for their base type?
  │   └── Liskov Substitution Principle (LSP)
  │       ├── Pre-conditions: subtype must NOT require more than base
  │       ├── Post-conditions: subtype must NOT deliver less than base
  │       ├── Invariants: subtype must preserve all base invariants
  │       ├── Fix: ensure subtype obeys the base contract
  │       └── Strongly tied to Interface Segregation Principle
  │
  ├── A wide interface forces implementors to define unused methods?
  │   └── Interface Segregation Principle (ISP)
  │       ├── Split into role-specific interfaces
  │       ├── Use composition over inheritance
  │       └── Use multiple small protocols/interfaces
  │
  └── High-level policy depends directly on low-level details?
      └── Dependency Inversion Principle (DIP)
          ├── Depend on abstractions, not concretions
          ├── Inject dependencies via constructor
          ├── Consider Adapter pattern to wrap external APIs/SDKs
          ├── Improves testability — swap real adapters with fakes
          └── See [design-patterns.md](design-patterns.md#adapter)
```

## When NOT to apply

A principle that adds more complexity than the problem it solves is the wrong principle. If code has no change pressure — stable, working, no testability issue — leave it alone.

---

## SRP — Facade

```typescript
// Bad: EmailService is responsible for sending, formatting, AND template loading
class EmailService {
  send(raw: any): void { ... }
  formatBody(data: any): string { ... }
  loadTemplate(name: string): string { ... }
}

// Good: Each concern has one reason to change
class TemplateEngine {
  load(name: string): Template { ... }
}

class EmailFormatter {
  format(template: Template, data: Record<string, unknown>): string { ... }
}

class EmailFacade {
  constructor(
    private engine: TemplateEngine,
    private formatter: EmailFormatter
  ) {}

  send(templateName: string, data: Record<string, unknown>): void {
    const template = this.engine.load(templateName)
    const body = this.formatter.format(template, data)
    // send logic
  }
}
```

---

## OCP — Strategy + Factory

```typescript
// Bad: Adding a new payment method requires changing existing code
class PaymentService {
  process(type: string, amount: number): void {
    if (type === "credit_card") { ... }
    if (type === "paypal") { ... }
  }
}

// Good: New methods added by implementing a new strategy, not by editing existing code
interface PaymentStrategy {
  process(amount: number): void
}

class CreditCardStrategy implements PaymentStrategy {
  process(amount: number): void { ... }
}

class PayPalStrategy implements PaymentStrategy {
  process(amount: number): void { ... }
}

class PaymentFactory {
  static create(type: string): PaymentStrategy {
    switch (type) {
      case "credit_card": return new CreditCardStrategy()
      case "paypal": return new PayPalStrategy()
      default: throw new Error(`Unknown payment type: ${type}`)
    }
  }
}

class PaymentService {
  process(type: string, amount: number): void {
    const strategy = PaymentFactory.create(type)
    strategy.process(amount)
  }
}
```

---

## LSP — Pre-conditions, Post-conditions, Invariants

```typescript
// Bad: Subclass strengthens pre-condition by requiring non-null
interface NotificationSender {
  send(recipient: string | null, message: string): void
}

class StrictSender implements NotificationSender {
  send(recipient: string | null, message: string): void {
    if (recipient == null) {
      throw new Error("Recipient required")  // stronger pre-condition than base
    }
    ...
  }
}

// Good: Subclass weakens pre-condition (accepts more) — within LSP bounds
class LoggingSender implements NotificationSender {
  send(recipient: string | null, message: string): void {
    if (recipient == null) {
      console.warn("No recipient — skipping send")
      return
    }
    // send logic
  }
}
```

---

## ISP — Interface Segregation

```typescript
// Bad: General-purpose interface forces RobotWorker to define eating and sleeping
interface Worker {
  work(): void
  eat(): void
  sleep(): void
}

class HumanWorker implements Worker {
  work(): void { ... }
  eat(): void { ... }
  sleep(): void { ... }
}

class RobotWorker implements Worker {
  work(): void { ... }
  eat(): void { throw new Error("Robots don't eat") }
  sleep(): void { throw new Error("Robots don't sleep") }
}

// Good: Role-specific interfaces
interface Workable {
  work(): void
}

interface Eatable {
  eat(): void
}

interface Sleepable {
  sleep(): void
}

class HumanWorker implements Workable, Eatable, Sleepable {
  work(): void { ... }
  eat(): void { ... }
  sleep(): void { ... }
}

class RobotWorker implements Workable {
  work(): void { ... }
}
```

---

## DIP — Adapter

```typescript
// Bad: Domain depends directly on external SDK
class ProjectService {
  private emailClient = new SendGridSDK()

  inviteMember(email: string): void {
    this.emailClient.sendEmail(email, "invite")
  }
}

// Good: Domain depends on abstraction; adapter wraps external SDK
interface NotificationPort {
  send(recipient: string, template: string): void
}

class SendGridAdapter implements NotificationPort {
  constructor(private client: SendGridSDK) {}

  send(recipient: string, template: string): void {
    this.client.sendEmail(recipient, template)
  }
}

class ProjectService {
  constructor(private notifications: NotificationPort) {}

  inviteMember(email: string): void {
    this.notifications.send(email, "invite")
  }
}
```

---

## Related

- [design-rules.md](design-rules.md) — when to apply SOLID and design patterns
- [design-patterns.md](design-patterns.md) — full pattern reference with structure diagrams
