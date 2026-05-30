---
name: contract-it
description: Defines concrete interface contracts — typed function signatures, API schemas, domain types, and event schemas — for the boundaries described or detected in the codebase. Writes actual source stubs for intra-codebase boundaries and schema documents for cross-service boundaries. Use when components need to agree on a shared interface before implementation begins, when parallel work requires a stable contract, or when the user says "define the interface", "write the contracts", "what does this port look like", or "define the API schema".
compatibility: Designed for Claude Code. Requires bash for script execution. Language and framework agnostic.
metadata:
  domain: interface-contracts
  version: "1.0"
---

Define concrete interface contracts for the boundaries described or detected in the codebase.

Contracts are typed artifacts — function signatures, request/response types, event schemas, domain types — not prose descriptions.
Do not include implementation logic in contracts.
Do not define contracts for boundaries that already have them unless asked to revise.

## When NOT to use this skill

- Interfaces already exist in the codebase for the described boundary — inspect first, skip if complete.
- The work is a single-component change with no new integration points or shared boundaries.
- The request is a code review or audit of existing contracts, not the creation of new ones.
- Implementation is already complete and contracts would only document existing code.
- No boundary has been described and the codebase provides no indication of what to contract.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load domain vocabulary. Use domain names consistently in all type names, field names, and method signatures.

2. Identify the boundaries to contract. Accept them from the user's description, inspect `docs/architecture/` if it exists, or discover them from existing code (port directories, integration test fixtures, call sites). Do not require architecture documents or PRDs — the codebase or the user's description is sufficient input.

3. For each boundary, check whether a contract already exists. Inspect port directories (`src/application/ports/`, `internal/ports/`, etc.), existing interface files, and schema files. Skip boundaries that already have complete contracts and note them in the summary.

4. Classify each new boundary: `port`, `api`, `event`, or `domain-type`. See [contract-rules.md — Boundary classification](references/contract-rules.md#boundary-classification).

5. Detect the project's language from `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, or `build.gradle`. Read [type-patterns.md](references/type-patterns.md) for the idiomatic contract pattern for the detected language.

6. Define each contract. Apply all rules in [contract-rules.md](references/contract-rules.md). For each:
   - Name it using [contract-rules.md — Naming conventions](references/contract-rules.md#naming-conventions)
   - Write the typed definition using [type-patterns.md](references/type-patterns.md)
   - State at least one invariant per [contract-rules.md — Invariant rules](references/contract-rules.md#invariant-rules)
   - Identify all known consumers (callers and implementers)

7. Determine the output location for each contract using [contract-rules.md — Output location rules](references/contract-rules.md#output-location-rules):
   - Intra-codebase port in a typed language with an existing source structure → write actual source stub
   - Cross-service, event schema, or source structure not yet established → run `bash scripts/ensure-contracts-dir.sh` and write `docs/contracts/<slug>.md` using [assets/contract-template.md](assets/contract-template.md)

8. Write the contract files.

9. Update `CONTEXT.md`. If new domain types, port names, or event names were defined or clarified, add them using the format in existing entries.

## Output files

For cross-service or pre-structure contracts:

```bash
bash scripts/ensure-contracts-dir.sh
```

- Contract document: `docs/contracts/<slug>.md`

For intra-codebase source stubs: write directly to the detected source ports directory. Do not create a docs file if a source stub is written.

## Before marking complete

- [ ] Every contract uses the project's domain vocabulary — no placeholder `<entity>` labels
- [ ] Every parameter and return type is explicitly named — no `any`, `object`, `dict`, or untyped signatures
- [ ] At least one invariant stated per contract
- [ ] All known consumers identified
- [ ] No implementation logic appears in any contract definition
- [ ] Existing contracts were checked before writing new ones

## Anti-patterns to avoid

**God interfaces**
- One interface per external capability. If a method could be removed without breaking all consumers, the interface mixes concerns — split it.

**Untyped contracts**
- Every field, parameter, and return type must be explicitly typed. An untyped contract implies agreement without enforcing it.

**Prose-only contracts**
- "The repository should find users" is not a contract. A typed method signature with an invariant is.

**Contracts derived from completed implementation**
- A contract written after implementation is documentation, not a contract. Write contracts before implementation so they can guide it.

**Implementation details in contracts**
- Do not include SQL queries, HTTP client calls, or serialization logic in a port interface. Contracts define behavior, not mechanism.

## Clarification protocol

Ask one question at a time. Each question must include numbered alternatives, one marked `(recommended)`, concrete and mutually exclusive.

Walk decisions in this order: boundary type → consumers and implementers → operations → parameter/return types → error conditions → invariants.

Inspect the codebase before asking — existing port files, type definitions, and test doubles often answer the question.

## Final response

After writing all contracts, summarize:

- Contract files written (source stubs or docs), with boundary type for each
- Consumers identified for each contract
- Contracts skipped because they already exist
- Open questions, if any
