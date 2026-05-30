---
name: architect-it
description: Produces a concrete architecture document for a project, feature, user story, or PRD. Generates hexagonal (ports-and-adapters) directory structures, port/adapter maps, Mermaid diagrams, tech-stack ADR stubs, and cross-cutting concern layouts. Use when asked to architect, design, blueprint, or scaffold a system — or when the user says "how should we structure this", "design the system", "create the architecture", "what's the project structure", "design a feature", or needs a technical blueprint before writing implementation tasks.
compatibility: Designed for Claude Code. Requires bash for script execution.
metadata:
  domain: software-architecture
  version: "1.0"
---

Produce a concrete architecture document for the given project, feature, or PRD.

Do not add layers, patterns, or abstractions not required by the described problem.
Do not invent requirements or assume scale constraints unless explicitly stated.

## When NOT to use this skill

- The request is a bug fix or a single-function change with no structural impact.
- An architecture document already exists and only an implementation plan is needed — use plan-it instead.
- The user wants implementation tasks without a design phase — use plan-it directly.
- The user is asking how existing code works, not how to structure new code.
- The scope is a single UI component or a single utility function with no domain logic.

## Core workflow

1. **Load vocabulary.** If `CONTEXT.md` exists at the project root, read it. Use its entity names, boundary names, and layer names consistently throughout the output.

2. **Classify project type.** Inspect existing source layout first (`ls src/`, `find . -name "package.json" -maxdepth 2`, `find . -name "pyproject.toml" -maxdepth 2`). If no code exists or the type is ambiguous, ask with numbered alternatives (one marked `recommended`). Types: `backend-api`, `frontend-spa`, `fullstack`, `data-pipeline`, `data-science`, `cli`, `library`. Read [architecture-rules.md — Project type patterns](references/architecture-rules.md#project-type-patterns) for canonical directory trees.

3. **Confirm tech stack.** Inspect config files. Ask only for what inspection cannot answer — never ask for language, framework, or persistence when `package.json`, `pyproject.toml`, `pom.xml`, `go.mod`, or `Cargo.toml` already answer it.

4. **State the scope.** Decide and state at the top of the output whether this is a `full-project`, a `bounded-context: <name>`, or a `feature-slice: <name>`. If unclear, ask — scoping the wrong level wastes the entire document.

5. **Build the directory structure.** Use the canonical hexagonal tree from [architecture-rules.md — Project type patterns](references/architecture-rules.md#project-type-patterns). Substitute actual domain entity names. Nest no deeper than 3 levels from `src/`. Annotate each non-obvious directory with a one-line inline comment (`# what lives here`).

6. **Map all ports and adapters.** Name every inbound adapter and every outbound port+adapter pair. Apply the naming convention and the one-adapter-per-port-is-default rule in [architecture-rules.md — Port/adapter mapping rules](references/architecture-rules.md#portadapter-mapping-rules). Do not create a port interface when only one implementation exists and no test double is needed.

7. **Select diagrams.** Read [diagram-selection.md](references/diagram-selection.md). Always include the mandatory hexagonal layers `flowchart`. Add conditional diagrams only when their trigger conditions are met. Hard cap: 3 diagrams total per document.

8. **Document cross-cutting concerns.** For each concern (auth, logging, error handling, config, tracing), state the approach and the layer it lives in. Omit concerns not implied by the project type or stated requirements.

9. **Identify ADR-worthy decisions.** For each irreversible, cross-cutting, or vendor-specific decision, write an ADR stub in `docs/adrs/` using [plan-it's ADR template](../plan-it/assets/adr-template.md). Apply the threshold in [architecture-rules.md — ADR threshold](references/architecture-rules.md#adr-threshold).

10. **Write the output document.** Run `bash scripts/ensure-architecture-dir.sh`, then write `docs/architecture/<feature-or-project-slug>.md` using [assets/architecture-template.md](assets/architecture-template.md) as the exact structure.

11. **Update CONTEXT.md.** If new domain terms were introduced or clarified, add them to `CONTEXT.md` using the format of existing entries.

## Output files

```bash
bash scripts/ensure-architecture-dir.sh
```

- Architecture document: `docs/architecture/<slug>.md`
- ADR stubs (if any): `docs/adrs/<NNN>-<slug>.md`

## Before marking complete

- [ ] Directory tree uses actual domain names, not placeholder `<entity>` labels
- [ ] Every node in the tree nests ≤3 levels from `src/`
- [ ] Every outbound port is named as an interface; every outbound adapter is named as a concrete type
- [ ] No layer contains a responsibility in its "Must NOT contain" column from [architecture-rules.md](references/architecture-rules.md#layer-rules)
- [ ] Hexagonal layers `flowchart` is present
- [ ] Maximum 3 diagrams in the document
- [ ] YAGNI row in "Principles Applied" names what was excluded and why
- [ ] ADR stubs written for every hard-to-reverse or cross-cutting tech decision

## Anti-patterns to avoid

**Over-engineering**
- Do not add `Manager`, `Handler`, `Helper`, `Util`, `Factory`, `Provider`, or `Facade` as directory names or layer names.
- Do not add event sourcing, CQRS, or read models unless the PRD explicitly requires audit history or complex projections.
- Do not split into microservices unless the PRD states independent deployment or different scaling requirements for specific components.
- Do not add a cache layer unless the PRD states a performance requirement that a cache would address.
- Do not add a message queue unless the PRD requires async processing or decoupling.

**Under-specification**
- Do not write "follow hexagonal architecture" without naming the actual ports and adapters.
- Do not write "use appropriate patterns" without stating which pattern and where.
- Do not leave `<entity>` placeholders in the final output — substitute real names.

**Layer violations**
- Domain entities must not import from adapters, infrastructure, or any framework package.
- Use cases must not import from HTTP routers, ORM models, or cloud SDKs.
- State these violations explicitly as risks if you find them in existing code.

## Clarification protocol

Ask one question at a time. Each question must include numbered alternatives (one marked `recommended`), concrete, and mutually exclusive. Walk decisions in this order: project type → scope → tech stack → key domain entities → deployment model.

Do not ask what the codebase already answers. Inspect first.

## Final response

After creating the files, summarize:

- Architecture scope stated (full-project / bounded-context / feature-slice)
- Project type detected
- Layers and what they own (one line each)
- Inbound adapters named
- Outbound ports and adapters named
- Diagrams included
- ADR stubs created, if any
- Open decisions, if any
- YAGNI exclusions stated
