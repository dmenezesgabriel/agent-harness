# Architecture Rules for architect-it

## Layer rules

Every project type uses the same four layers. Names differ; rules do not.

| Layer | Owns | Must NOT contain |
|---|---|---|
| `domain/` | Entities, value objects, domain events, aggregate roots, domain rules | Framework imports, ORM models, HTTP types, DB queries, cloud SDK calls |
| `application/` | Use cases, inbound port interfaces, outbound port interfaces, DTOs | HTTP request/response types, SQL, ORM annotations, cloud SDK calls |
| `adapters/inbound/` | Entry-point translation (HTTP, CLI, events → use-case calls) | Business rules, domain object construction, direct DB calls |
| `adapters/outbound/` | Implementations of outbound ports (DB, external APIs, queues) | Business rules, HTTP routing, use-case logic |
| `infrastructure/` | DI wiring, config loading, server bootstrap, migration runner | Business rules, adapter logic, domain logic |

**Dependency rule**: `domain` ← `application` ← `adapters` ← `infrastructure`. Never reverse. `domain` imports nothing from this project.

## Project type patterns

Use the canonical tree for the detected type. Replace `<entity>` with actual domain names. Replace file extensions with the project language (`.ts`, `.py`, `.go`, `.java`, etc.).

---

### backend-api

REST or GraphQL API with a database backend.

```
src/
├── domain/
│   └── <entity>/
│       ├── <Entity>.<ext>           # entity with business rules
│       ├── <Entity>Events.<ext>     # domain events (omit if not event-driven)
│       └── <Value>.<ext>            # value objects
├── application/
│   ├── ports/
│   │   └── outbound/
│   │       └── <Entity>Repo.<ext>   # repository interface
│   └── use-cases/
│       └── <action>-<entity>/
│           ├── <ActionEntity>.<ext>
│           └── <ActionEntity>Dto.<ext>
├── adapters/
│   ├── inbound/
│   │   ├── http/
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   └── events/                  # omit if not event-driven
│   └── outbound/
│       ├── persistence/
│       │   └── <Pg|Mongo><Entity>Repo.<ext>
│       └── external/                # omit if no external APIs
│           └── <Service>Client.<ext>
└── infrastructure/
    ├── config.<ext>
    ├── container.<ext>              # DI wiring
    └── server.<ext>                 # framework bootstrap
tests/
├── unit/
├── integration/
└── e2e/
```

---

### frontend-spa

React, Vue, Angular, or Svelte single-page application.

```
src/
├── domain/
│   └── <entity>/
│       ├── <Entity>.<ext>
│       └── <Entity>Validator.<ext>
├── application/
│   ├── ports/
│   │   └── outbound/
│   │       └── <Entity>ApiPort.<ext>   # API interface the app needs
│   └── use-cases/
│       └── <action>-<entity>/
│           └── <ActionEntity>.<ext>
├── adapters/
│   ├── inbound/
│   │   └── ui/
│   │       ├── pages/
│   │       └── components/
│   └── outbound/
│       ├── api/
│       │   └── <Entity>ApiAdapter.<ext>
│       └── storage/                    # localStorage/IndexedDB (omit if unused)
└── infrastructure/
    ├── config.<ext>
    └── router.<ext>
tests/
├── unit/
├── component/
└── e2e/
```

---

### fullstack

Monorepo: separate `backend-api` and `frontend-spa` apps, shared packages.

```
apps/
├── api/                   # backend-api structure above
└── web/                   # frontend-spa structure above
packages/
├── domain/                # shared domain types and value objects
│   └── src/
├── ui/                    # shared UI components (omit if none)
│   └── src/
└── config/                # shared configuration schemas
    └── src/
docs/
├── architecture/
└── adrs/
```

Add a package only when ≥2 apps share the same code. Do not create packages speculatively.

---

### data-pipeline

Batch or streaming ETL/ELT pipeline.

```
src/
├── domain/
│   ├── schema/
│   │   └── <Entity>Schema.<ext>    # data contracts / validation schemas
│   └── rules/
│       └── <Transform>Rule.<ext>   # transformation and quality rules
├── application/
│   ├── ports/
│   │   ├── inbound/
│   │   │   └── <Source>ReaderPort.<ext>
│   │   └── outbound/
│   │       └── <Sink>WriterPort.<ext>
│   └── pipelines/
│       └── <PipelineName>.<ext>    # orchestration: read → transform → write
├── adapters/
│   ├── inbound/
│   │   ├── <S3|GCS>Reader.<ext>
│   │   ├── <Kafka|Pubsub>Consumer.<ext>
│   │   └── <Http>Reader.<ext>      # omit sources not in scope
│   └── outbound/
│       ├── <BigQuery|Redshift>Writer.<ext>
│       └── <Kafka|Pubsub>Publisher.<ext>
└── infrastructure/
    ├── config.<ext>
    ├── scheduler.<ext>
    └── monitoring.<ext>
tests/
├── unit/
└── integration/
```

---

### data-science

ML model training, evaluation, and deployment pipeline.

```
src/
├── domain/
│   ├── features/
│   │   └── <Feature>Definition.<ext>   # feature schema and derivation logic
│   └── metrics/
│       └── <Metric>.<ext>              # evaluation metric definitions
├── application/
│   ├── ports/
│   │   ├── inbound/
│   │   │   └── DatasetPort.<ext>       # dataset loading interface
│   │   └── outbound/
│   │       ├── ModelRegistryPort.<ext>
│   │       └── FeatureStorePort.<ext>
│   └── experiments/
│       └── <ExperimentName>.<ext>      # training orchestration
├── adapters/
│   ├── inbound/
│   │   ├── <Local|S3>DatasetAdapter.<ext>
│   │   └── <StreamAdapter>.<ext>       # omit if batch-only
│   └── outbound/
│       ├── <MLflow|WandB>ModelRegistry.<ext>
│       └── <Feast|Tecton>FeatureStore.<ext>   # omit if no feature store
└── infrastructure/
    ├── config.<ext>
    ├── training_runner.<ext>
    └── monitoring.<ext>
notebooks/                              # exploratory only — not production code
tests/
├── unit/
└── integration/
```

---

### cli

Command-line tool with subcommands.

```
src/
├── domain/
│   └── <entity>/
│       └── <Entity>.<ext>
├── application/
│   ├── ports/
│   │   └── outbound/
│   │       └── <Resource>Port.<ext>
│   └── commands/
│       └── <command-name>/
│           └── <CommandName>.<ext>     # business logic for the command
├── adapters/
│   ├── inbound/
│   │   └── cli/
│   │       └── <command-name>.<ext>    # arg parsing → calls application
│   └── outbound/
│       └── <Filesystem|Http|Db>Adapter.<ext>
└── infrastructure/
    ├── config.<ext>
    └── container.<ext>
tests/
├── unit/
└── integration/
```

---

### library

Reusable library with a public API surface.

```
src/
├── domain/
│   └── <entity>/
│       └── <Entity>.<ext>
├── application/
│   └── <feature>/
│       └── <FeatureFunction>.<ext>     # public API functions
├── adapters/
│   └── outbound/
│       └── <ExternalDep>Adapter.<ext>  # wrap external dependencies
└── index.<ext>                         # public exports only — no internals exposed
tests/
├── unit/
└── integration/
```

---

## Port/adapter mapping rules

### Naming

- Port (interface): `<Entity>Repository`, `<Service>Port`, `<Event>Publisher`, `<Resource>Reader`, `<Resource>Writer`
- Adapter (implementation): `<Tech><Entity>Repository` (e.g., `PgUserRepository`), `<Tech><Service>Client` (e.g., `SendgridEmailClient`)

### One adapter per port is the default

Do not create a port interface when there is only one concrete implementation and no test double is needed — that is YAGNI. Create a port when:
- ≥2 concrete implementations exist or are planned in the PRD
- The implementation must be swapped for a test double in unit tests
- The dependency crosses a system or process boundary

### Inbound adapters do not implement interfaces

HTTP controllers, CLI parsers, and event consumers call use cases directly. They are not behind an interface — they are the entry point. Only outbound dependencies (things the app calls out to) need port interfaces.

## ADR threshold

Write an ADR stub in `docs/adrs/` for any decision that is:

- Hard to reverse: choice of database engine, ORM, message broker, cloud provider, API protocol (REST vs GraphQL vs gRPC)
- Cross-cutting: authentication strategy, error handling contract, logging format, distributed tracing approach
- Boundary-defining: monolith vs microservices, sync vs async communication, event sourcing vs CRUD

Do NOT write an ADR for:
- Naming conventions within a single file
- Library versions
- Folder organization details that can be changed without cascading impact

## SOLID, DRY, KISS, YAGNI enforcement

Apply these as constraints on the directory structure and layer map, not as post-hoc commentary:

| Principle | Concrete check |
|---|---|
| Single Responsibility | Each use case touches exactly one aggregate root |
| Open/Closed | New adapters plug into existing ports without changing application code |
| Liskov Substitution | Adapter implementations are fully interchangeable behind their port |
| Interface Segregation | Outbound ports are narrow: one port per external capability, not one god-interface |
| Dependency Inversion | `domain/` and `application/` import nothing from `adapters/` or `infrastructure/` |
| DRY | Shared domain logic lives in `domain/` or `application/`, not duplicated across adapters |
| KISS | Start with a monolith; split only when a PRD requirement forces it |
| YAGNI | Exclude any layer, port, or adapter not required by a stated requirement — name what was excluded and why |
