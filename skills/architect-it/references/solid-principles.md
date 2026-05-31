# SOLID, DRY, KISS, YAGNI Reference

Apply these as structural constraints on the directory and layer map — not as post-hoc commentary.

| Principle | Concrete check | Violating signal |
|---|---|---|
| Single Responsibility | Each orchestration unit (use case, pipeline, feature slice) operates on one cohesive concern and has one reason to change | A use case touches ≥2 unrelated entities or a pipeline stage both validates and transforms |
| Open/Closed | New I/O adapters (sources, sinks, API clients, DB repos) slot in without modifying orchestration or domain code | Adding a new data source requires editing a pipeline or use case file |
| Liskov Substitution | All implementations of a port interface are fully interchangeable — the orchestration layer cannot tell them apart | A use case `instanceof`-checks the adapter it receives, or an adapter's behavior changes the caller's control flow |
| Interface Segregation | Ports and contracts are narrow: one interface per external capability, never a god-interface covering multiple concerns | A single port interface has methods for both reading and writing, or covers both user auth and profile |
| Dependency Inversion | Core and orchestration layers import nothing from adapters or infrastructure — the dependency always points inward | A domain entity imports an ORM model, or a use case imports a cloud SDK |
| DRY | Shared domain logic lives in `domain/`, shared utilities in a `shared/` or `lib/` module — never duplicated across adapters | The same validation rule appears in two adapter files |
| KISS | Start with a single deployable unit; split only when an explicit requirement (independent scaling, separate deploy cadence) forces it | Microservices or event sourcing added before the PRD states a concrete need for them |
| YAGNI | Exclude any layer, port, interface, or directory not required by a stated requirement — name what was excluded and why | A `cache/` layer or `events/` directory added without a performance requirement or async requirement in the PRD |
