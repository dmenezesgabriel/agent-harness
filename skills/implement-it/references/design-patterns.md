# Design Patterns Reference

Language-agnostic. Each pattern: intent, ASCII structure diagram, conditions for use, and anti-pattern signals.

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
- You want to isolate object construction from the code that uses it

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
- You need to swap an entire product family at runtime (e.g., different UI themes, different cloud providers)

**Watch out**:
- Adding a new product type requires changing the abstract interface and all concrete factories — evaluate whether the family is truly stable before committing

---

### Builder

**Intent**: Separate the construction of a complex object from its representation.

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

**Watch out**:
- Overkill for objects with fewer than ~4 fields — use a plain constructor or config struct instead

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
- There must be exactly one instance (e.g., a config registry, a connection pool)
- That instance must be accessible from many places

**Watch out**:
- Global state makes unit testing difficult — prefer dependency injection with a single instance managed at the composition root

---

## Structural

### Adapter

**Intent**: Convert the interface of a class into another interface that clients expect.

**Structure**:
```
Client → Target (interface)
                ▲
            Adapter
              └── wraps → Adaptee
```

**When to use**:
- You are wrapping a third-party library behind a project-owned interface
- You need to make several incompatible classes work through a single interface

**Watch out**:
- Excessive adapters add indirection — if you control both sides, change the interface directly instead

---

### Decorator

**Intent**: Attach additional responsibilities to an object dynamically, as an alternative to subclassing.

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
- You are integrating a third-party library and want one stable entry point

**Watch out**:
- A facade that grows to expose everything in the subsystem no longer simplifies — it becomes a wrapper with the same coupling problem

---

### Composite

**Intent**: Compose objects into tree structures to represent part-whole hierarchies.

**Structure**:
```
Component (interface)
  ├── Leaf          (no children)
  └── Composite     (has children: Component[])
        └── operation() → calls operation() on each child
```

**When to use**:
- You need to represent hierarchies (file system trees, UI component trees, org charts)
- Clients should ignore the difference between a single object and a group

**Watch out**:
- Making the interface too general to accommodate both Leaf and Composite can restrict operations that only make sense on one type

---

## Behavioral

### Strategy

**Intent**: Define a family of algorithms, encapsulate each one, and make them interchangeable.

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

**Watch out**:
- If only one strategy is ever used in practice, the abstraction adds indirection without benefit — inline the algorithm instead

---

### Observer

**Intent**: Define a one-to-many dependency so that when one object changes state, all dependents are notified automatically.

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
- A change in one object requires updating others and you don't know how many need to change
- You want loose coupling between the event source and its consumers

**Watch out**:
- Unexpected update cascades — keep observers side-effect-free or idempotent
- Memory leaks when observers are not detached after the subject is destroyed

---

### Command

**Intent**: Encapsulate a request as an object to support queuing, logging, and undoable operations.

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
- You need to support undo/redo or queue/schedule operations
- You need to parameterise objects with operations (e.g., menu items, queue tasks)

**Watch out**:
- Command objects proliferate quickly — if operations do not need queuing, undo, or logging, a plain function call is simpler

---

### Template Method

**Intent**: Define the skeleton of an algorithm in a base class, deferring some steps to subclasses.

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

**Intent**: Pass a request along a chain of handlers. Each handler decides to process or pass it on.

**Structure**:
```
Handler (interface)
  ├── setNext(Handler)
  └── handle(Request)
        ▲
  HandlerA → HandlerB → HandlerC → (nil / end)
```

**When to use**:
- More than one object may handle a request, and the handler is not known in advance
- The set of handlers and their order should be configurable at runtime (e.g., middleware pipelines, validation chains)

**Watch out**:
- A request that reaches the end of the chain without being handled is a silent failure — always define a terminal handler or log unhandled requests
