# Design Patterns Reference

Language-agnostic. Each pattern follows the same structure: intent, ASCII structure diagram, conditions for use, and anti-pattern signals.

---

## Creational

### Factory Method

**Intent**: Define an interface for creating an object, but let subclasses or implementations decide which class to instantiate.

**Structure**:
```
Creator
  └── create() → Product
        ▲
ConcreteCreatorA          ConcreteCreatorB
  └── create() → ProductA   └── create() → ProductB
```

**When to use**:
- The exact type of object to create is determined at runtime
- You want to isolate object construction from the code that uses the object
- A class cannot anticipate the type of objects it must create

**Watch out**:
- Can lead to class proliferation when every variant gets its own creator subclass — prefer a parameterised factory function when variants are simple

---

### Abstract Factory

**Intent**: Provide an interface for creating families of related objects without specifying their concrete classes.

**Structure**:
```
AbstractFactory
  ├── createButton() → Button
  └── createCheckbox() → Checkbox
        ▲                    ▲
WebFactory              MobileFactory
  ├── createButton()    ├── createButton()
  └── createCheckbox()  └── createCheckbox()
```

**When to use**:
- A system must be independent of how its products are created
- You need to enforce that related objects (a "family") are always used together
- You want to swap an entire product family at runtime (e.g., different UI themes, different cloud providers)

**Watch out**:
- Adding a new product type to the family requires changing the abstract interface and all concrete factories — evaluate whether the family is truly stable before committing

---

### Builder

**Intent**: Separate the construction of a complex object from its representation, so the same construction process can create different representations.

**Structure**:
```
Director
  └── construct(builder)
            │
         Builder (interface)
           ├── buildPartA()
           ├── buildPartB()
           └── getResult() → Product

ConcreteBuilderX implements Builder
```

**When to use**:
- Construction involves many optional parameters (avoids telescoping constructors)
- The same construction steps should produce different representations
- You need fine-grained control over the construction sequence

**Watch out**:
- Overkill for objects with fewer than ~4 fields — use a plain constructor or a config struct instead
- The builder itself can become a god object if it accumulates too many methods

---

### Singleton

**Intent**: Ensure a class has only one instance and provide global access to it.

**Structure**:
```
Singleton
  ├── -instance: Singleton
  ├── -constructor()
  └── +getInstance() → Singleton
```

**When to use**:
- There must be exactly one instance of a class (e.g., a logger, a config registry, a connection pool)
- That instance must be accessible from many places

**Watch out**:
- Global state makes unit testing difficult — prefer dependency injection with a single instance managed at the composition root
- Often a sign that dependency injection is not in use; treat as a last resort

---

## Structural

### Adapter

**Intent**: Convert the interface of a class into another interface that clients expect. Lets incompatible interfaces work together.

**Structure**:
```
Client → Target (interface)
                ▲
            Adapter
              └── wraps → Adaptee
```

**When to use**:
- You want to use an existing class but its interface does not match what you need
- You are wrapping a third-party library behind a project-owned interface (see Dependency Inversion)
- You need to make several incompatible classes work through a single interface

**Watch out**:
- Excessive adapters add indirection — if you control both sides, change the interface directly instead

---

### Decorator

**Intent**: Attach additional responsibilities to an object dynamically, as an alternative to subclassing for extending functionality.

**Structure**:
```
Component (interface)
  ├── ConcreteComponent
  └── BaseDecorator (wraps Component)
        └── ConcreteDecoratorA
        └── ConcreteDecoratorB
```

**When to use**:
- You need to add behaviour to individual objects without affecting others of the same class
- Extension by subclassing would produce an explosion of subclasses for every combination
- Behaviour should be composable and removable at runtime (e.g., logging, retry, caching wrappers)

**Watch out**:
- Deeply stacked decorators produce hard-to-debug call chains — keep decorator depth shallow (≤3)

---

### Facade

**Intent**: Provide a simplified interface to a complex subsystem.

**Structure**:
```
Client → Facade
           ├── calls SubsystemA
           ├── calls SubsystemB
           └── calls SubsystemC
```

**When to use**:
- A subsystem has grown complex and callers only need a small slice of its capabilities
- You want to layer a subsystem so higher-level clients are shielded from internals
- You are integrating a third-party library and want one stable entry point

**Watch out**:
- A facade that grows to expose everything in the subsystem is no longer a facade — it is a wrapper with the same coupling problem

---

### Composite

**Intent**: Compose objects into tree structures to represent part-whole hierarchies. Lets clients treat individual objects and compositions uniformly.

**Structure**:
```
Component (interface)
  ├── Leaf          (no children)
  └── Composite     (has children: Component[])
        └── operation() → calls operation() on each child
```

**When to use**:
- You need to represent hierarchies (file system trees, UI component trees, org charts)
- Clients should be able to ignore the difference between a single object and a group

**Watch out**:
- Making the interface too general to accommodate both Leaf and Composite can make it harder to restrict operations that only make sense on one type

---

## Behavioral

### Strategy

**Intent**: Define a family of algorithms, encapsulate each one, and make them interchangeable. Lets the algorithm vary independently from the clients that use it.

**Structure**:
```
Context
  └── -strategy: Strategy (interface)
        └── execute()
              ▲
  StrategyA       StrategyB       StrategyC
```

**When to use**:
- Multiple variants of an algorithm exist and must be switchable at runtime
- You want to eliminate `if/switch` chains selecting algorithm variants
- An algorithm uses data that clients should not know about (encapsulate it)

**Watch out**:
- If only one strategy is ever used in practice, the abstraction adds indirection without benefit — inline the algorithm instead

---

### Observer

**Intent**: Define a one-to-many dependency between objects so that when one object changes state, all its dependents are notified automatically.

**Structure**:
```
Subject (Observable)
  ├── attach(Observer)
  ├── detach(Observer)
  └── notify()
          │
     Observer (interface)
       └── update()
             ▲
   ConcreteObserverA    ConcreteObserverB
```

**When to use**:
- A change in one object requires updating others and you don't know how many objects need to change
- Objects should be able to notify others without making assumptions about who those objects are
- You want loose coupling between the event source and its consumers

**Watch out**:
- Unexpected update cascades — an observer that triggers another update can cause cycles; keep observers side-effect-free or idempotent
- Memory leaks when observers are not detached after the subject is destroyed

---

### Command

**Intent**: Encapsulate a request as an object, thereby letting you parameterise clients with different requests, queue or log requests, and support undoable operations.

**Structure**:
```
Invoker
  └── execute(Command)
            │
       Command (interface)
         └── execute()
               ▲
  ConcreteCommandA    ConcreteCommandB
    └── execute()       └── execute()
          │
       Receiver (does the actual work)
```

**When to use**:
- You need to parameterise objects with operations (e.g., menu items, buttons, queue tasks)
- You need to support undo/redo
- You need to queue, schedule, or log operations

**Watch out**:
- Command objects proliferate quickly — if operations do not need queuing, undo, or logging, a plain function call is simpler

---

### Template Method

**Intent**: Define the skeleton of an algorithm in a base class, deferring some steps to subclasses. Lets subclasses redefine certain steps without changing the algorithm's overall structure.

**Structure**:
```
AbstractClass
  └── templateMethod()   ← fixed sequence
        ├── step1()      ← concrete (shared)
        ├── step2()      ← abstract (subclass fills in)
        └── step3()      ← hook (optional override)

ConcreteClass extends AbstractClass
  └── step2()   ← specific implementation
```

**When to use**:
- Multiple classes share the same algorithm structure but differ in specific steps
- You want to control which parts of an algorithm subclasses can override

**Watch out**:
- Inheritance couples the subclass to the base — if the algorithm skeleton changes frequently, prefer Strategy (composition) over Template Method (inheritance)

---

### Chain of Responsibility

**Intent**: Pass a request along a chain of handlers. Each handler decides to process the request or pass it to the next handler in the chain.

**Structure**:
```
Handler (interface)
  ├── setNext(Handler)
  └── handle(Request)
        ▲
  HandlerA → HandlerB → HandlerC → (nil / end)
```

**When to use**:
- More than one object may handle a request, and the handler is not known a priori
- You want to issue a request to one of several objects without specifying the receiver explicitly
- The set of handlers and their order should be configurable at runtime (e.g., middleware pipelines, validation chains)

**Watch out**:
- A request that reaches the end of the chain without being handled is a silent failure — always define a terminal handler or log unhandled requests
