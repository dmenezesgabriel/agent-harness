# Architecture Rules for architect-it

## Architectural principles

These rules hold for every project type. Directory names differ by domain idiom; dependency direction and separation rules do not.

### Dependency direction

Core logic never imports from I/O, frameworks, or infrastructure. The invariant across all project types:

```
core ← orchestration ← adapters ← infrastructure
```

Each project type expresses this with its own idiomatic names:

| Project type | Core | Orchestration | Adapters | Infrastructure |
|---|---|---|---|---|
| `backend-api`, `cli`, `library` | `domain/` | `application/` | `adapters/` | `infrastructure/` |
| `frontend-spa` | `domain/` | `features/` | `pages/`, `shared/` | `app/` |
| `data-pipeline` | `domain/` | `pipelines/` | `sources/`, `sinks/` | `infrastructure/` |
| `data-science` | `domain/` | `features/`, `models/` | `pipelines/` | `infrastructure/` |

### Separation invariants (all project types)

| Layer role | Owns | Must NOT contain |
|---|---|---|
| Core / domain | Entities, value objects, rules, schemas, metrics — pure logic | Framework imports, ORM models, HTTP types, DB queries, SDK calls |
| Orchestration | Use cases, pipelines, experiment runs, feature logic — coordinates core only | HTTP types, SQL, ORM annotations, cloud SDK calls, UI framework code |
| Adapters | I/O translation: HTTP, DB, cloud, UI rendering, file I/O | Business rules, domain construction, cross-adapter dependencies |
| Infrastructure | DI wiring, config loading, bootstrap, scheduling | Business rules, adapter logic, domain logic |

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

Single-page application. Framework-agnostic feature-based vertical slice structure, as adopted by the broader SPA community (React, Vue, Angular, Svelte, etc.).

```
src/
├── domain/                  # pure business logic — no UI, no framework imports
│   └── <entity>/
│       ├── <Entity>.<ext>
│       └── <Entity>Validator.<ext>
├── features/                # vertical slices — one directory per user-facing capability
│   └── <feature>/
│       ├── api.<ext>        # outbound HTTP/GraphQL calls scoped to this feature
│       ├── state.<ext>      # local state and business logic — no UI framework dependency
│       ├── <Feature>.<ext>  # root view component for this feature
│       └── components/      # private sub-components — not exported outside this feature
├── pages/                   # route-level views — compose features, own no business logic
│   └── <Page>.<ext>
├── shared/                  # cross-feature reusables — no business logic
│   ├── ui/                  # generic, stateless UI components
│   └── lib/                 # utilities, formatters, constants
└── app/                     # bootstrap, routing, global config and providers
    ├── config.<ext>
    └── router.<ext>
tests/
├── unit/
├── component/
└── e2e/
```

**Dependency rule**: `domain` ← `features` ← `pages` ← `app`. `shared` is imported by any layer but must not import from `features`, `pages`, or `app`. A feature must not import from another feature — cross-feature data flows through `domain/`.

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

Batch or streaming ETL/ELT pipeline. `sources` and `sinks` are the universal industry terms for inbound and outbound adapters in data engineering.

```
src/
├── domain/                  # data contracts, transformation rules, quality rules
│   ├── schemas/
│   │   └── <Entity>Schema.<ext>         # input/output data contracts and validation
│   └── rules/
│       └── <Transform>Rule.<ext>        # pure transformation and quality logic
├── pipelines/               # orchestration: read → transform → write
│   ├── ports/               # reader/writer interfaces this pipeline depends on
│   │   ├── <Source>ReaderPort.<ext>
│   │   └── <Sink>WriterPort.<ext>
│   └── <PipelineName>.<ext>
├── sources/                 # inbound adapters — implement <Source>ReaderPort
│   └── <SourceName>Reader.<ext>         # omit sources not in scope
├── sinks/                   # outbound adapters — implement <Sink>WriterPort
│   └── <SinkName>Writer.<ext>           # omit sinks not in scope
└── infrastructure/          # config, scheduler, monitoring, DI wiring
    ├── config.<ext>
    ├── scheduler.<ext>
    └── monitoring.<ext>
tests/
├── unit/
└── integration/
```

**Dependency rule**: `domain` ← `pipelines` ← `sources/sinks` ← `infrastructure`. `pipelines/` owns the port interfaces because it defines the abstractions it needs — sources and sinks implement those interfaces without knowing the pipeline internals.

---

### data-science

ML model training, evaluation, and serving. Structure follows the Cookiecutter Data Science v2 convention, extended with a clean dependency direction.

```
data/
├── raw/                     # immutable source data — never overwritten by code
├── interim/                 # partially processed, always re-derivable from raw
└── processed/               # final, model-ready inputs
notebooks/                   # exploration only — never imported by src/
src/
├── domain/                  # data contracts, feature schemas, evaluation metric logic
│   ├── schemas/
│   │   └── <Entity>Schema.<ext>         # input/output contracts and validation rules
│   └── metrics/
│       └── <Metric>.<ext>               # metric computation (pure functions)
├── features/                # feature engineering — pure transformations on domain data
│   └── <feature-group>/
│       └── <FeatureName>.<ext>
├── models/                  # model definitions, training logic, evaluation
│   └── <model-name>/
│       ├── train.<ext>
│       └── evaluate.<ext>
├── pipelines/               # end-to-end orchestration: load → featurize → train or infer
│   └── <PipelineName>.<ext>
└── infrastructure/          # I/O: data loaders, model registry clients, config
    ├── loaders/
    │   └── <Source>Loader.<ext>         # omit sources not in scope
    ├── registry.<ext>                   # model registry client
    └── config.<ext>
models/                      # serialized model artifacts — outputs of training pipelines
reports/                     # generated figures and evaluation outputs
tests/
├── unit/
└── integration/
```

**Dependency rule**: `domain` ← `features/models` ← `pipelines` ← `infrastructure`. `features/` and `models/` import from `domain/` only. `pipelines/` orchestrates but does not own business rules. `infrastructure/` wires I/O and is the only layer allowed to import third-party ML framework clients.

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
| Single Responsibility | Each orchestration unit (use case, pipeline, feature slice) operates on one cohesive concern and has one reason to change |
| Open/Closed | New I/O adapters (sources, sinks, API clients, DB repos) slot in without modifying orchestration or domain code |
| Liskov Substitution | All implementations of a port interface are fully interchangeable — the orchestration layer cannot tell them apart |
| Interface Segregation | Ports and contracts are narrow: one interface per external capability, never a god-interface covering multiple concerns |
| Dependency Inversion | Core and orchestration layers import nothing from adapters or infrastructure — the dependency always points inward |
| DRY | Shared domain logic lives in `domain/`, shared utilities in a `shared/` or `lib/` module — never duplicated across adapters |
| KISS | Start with a single deployable unit; split only when an explicit requirement (independent scaling, separate deploy cadence) forces it |
| YAGNI | Exclude any layer, port, interface, or directory not required by a stated requirement — name what was excluded and why |
