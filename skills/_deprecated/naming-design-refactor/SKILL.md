---
name: naming-design-refactor
description: Improve names in code to increase clarity, domain alignment, maintainability, searchability, and design intent without changing behavior.
---

## Purpose

Refactor naming across code to make intent, responsibility, ownership, domain meaning, and abstraction level explicit.

Use this skill for variables, functions, methods, classes, modules, packages, components, services, interfaces, ports, adapters, tests, files, directories, configuration keys, events, commands, queries, DTOs, and database-facing names.

This skill is language-agnostic.

## Core Principle

A good name reveals intent, scope, responsibility, abstraction level, and domain meaning.

Rename only when the new name improves comprehension, reduces ambiguity, exposes design intent, or aligns code with the domain language.

Do not rename for style preference alone.

## Review Principles

### Intent-Revealing Names

Check whether names explain what the code represents or does.

Flag vague, generic, misleading, abbreviated, or implementation-centered names.

Prefer names that expose purpose, behavior, role, or domain meaning.

Key terms: intent-revealing name, semantic clarity, readability, ambiguity, domain intent, self-documenting code.

### Domain Language

Check whether names match the business domain and user-facing concepts.

Flag technical names where domain names would be clearer, inconsistent terminology, synonyms for the same concept, and one term used for different meanings.

Prefer consistent names from the ubiquitous language of the domain.

Key terms: ubiquitous language, domain model, bounded context, semantic consistency, terminology drift, concept integrity.

### Responsibility and Role

Check whether the name matches the unit’s actual responsibility.

Flag names that are too broad, too narrow, outdated, or inconsistent with behavior.

Prefer names that identify the role: policy, rule, service, factory, repository, adapter, mapper, validator, parser, formatter, handler, controller, use case, command, query, event.

Key terms: responsibility alignment, role clarity, naming drift, behavioral contract, ownership.

### Abstraction Level

Check whether names are at the correct abstraction level.

Flag names that mix domain language with low-level implementation details, or high-level abstractions named after current technical mechanisms.

Prefer domain names in core logic and mechanism names only in infrastructure or implementation detail boundaries.

Key terms: abstraction level, implementation detail, policy/detail separation, infrastructure leakage, leaky abstraction.

### Precision and Specificity

Check whether names are specific enough without being noisy.

Flag names like `data`, `info`, `item`, `object`, `manager`, `processor`, `helper`, `utils`, `common`, `temp`, `result`, or `handler` when they hide meaning.

Prefer precise names that describe the concept, operation, or result.

Key terms: semantic precision, generic name, noise word, filler word, naming smell, weak noun, weak verb.

### Consistency

Check whether similar concepts are named consistently across the codebase.

Flag inconsistent suffixes, prefixes, casing, tense, pluralization, verbs, domain terms, file names, and test names.

Prefer one term per concept and one concept per term within a bounded context.

Key terms: naming convention, semantic consistency, lexical consistency, synonym drift, homonym conflict.

### Searchability

Check whether names are easy to search, trace, and refactor safely.

Flag short abbreviations, overloaded names, generated-looking names, and names shared by unrelated concepts.

Prefer distinctive, stable, searchable names for important domain concepts and public contracts.

Key terms: searchability, traceability, grepability, symbol uniqueness, rename safety.

### Boolean Names

Check whether boolean names read clearly as true or false.

Flag ambiguous booleans, negative booleans, and names that do not express a predicate.

Prefer `is`, `has`, `can`, `should`, `requires`, `allows`, or `supports` when appropriate.

Key terms: predicate name, positive boolean, boolean clarity, double negative, state flag.

### Function and Method Names

Check whether function names describe observable behavior.

Flag vague verbs like `handle`, `process`, `manage`, `do`, `run`, `execute`, or `perform` when the actual behavior is more specific.

Prefer verb phrases that describe the action and outcome.

Key terms: command-query separation, side effect, pure function, action verb, behavioral naming.

### Type, Class, and Module Names

Check whether structural names describe a coherent concept or role.

Flag god names, umbrella names, utility names, and names that hide mixed responsibilities.

Prefer names that reflect cohesive ownership and bounded responsibility.

Key terms: cohesion, single responsibility, module boundary, class responsibility, package intent.

### Test Names

Check whether tests describe behavior, condition, and expected outcome.

Flag tests named after implementation details, private methods, or vague scenarios.

Prefer behavior-oriented names that clarify the rule being protected.

Key terms: behavior specification, executable specification, given-when-then, observable behavior, regression test.

## Review Rules

Be concrete, falsifiable, and code-specific.

Do not say:

- Improve names.
- Make naming clearer.
- Rename this.
- Use better terminology.
- This name is bad.

Instead explain:

- Which name is ambiguous.
- Which concept it hides.
- Which responsibility it misrepresents.
- Which domain term should replace it.
- Which abstraction level is wrong.
- Which names conflict or drift.
- Which rename improves searchability or boundary clarity.
- Whether the rename is behavior-preserving.

Do not rename everything.

Prioritize names that affect public contracts, domain concepts, architectural boundaries, test readability, dangerous ambiguity, or frequent navigation.

Avoid churn where the current name is local, clear enough, and low impact.

## Output Format

For each finding, use:

### Finding: precise naming issue

Priority: High | Medium | Low

Category: Intent | Domain Language | Responsibility | Abstraction Level | Precision | Consistency | Searchability | Boolean | Function | Type | Test

Current name:
State the current name.

Issue:
Describe the exact naming problem.

Evidence:
Point to the function, class, module, variable, test, file, or concept.

Design impact:
Explain the consequence: ambiguity, wrong responsibility, weak searchability, domain mismatch, abstraction leakage, inconsistent terminology, or harder refactoring.

Recommended name:
Provide the proposed replacement.

Rationale:
Explain why the new name is more precise.

Scope:
State whether the rename should be local, module-wide, bounded-context-wide, or public-contract-wide.

## Refactoring Strategy

Prefer behavior-preserving renames.

Recommended order:

1. Identify domain concepts and existing terminology.
2. Detect ambiguous, generic, misleading, or outdated names.
3. Rename public contracts and core domain concepts carefully.
4. Rename local symbols when they improve immediate readability.
5. Align file, module, class, and test names with responsibility.
6. Remove synonym drift within the same bounded context.
7. Keep different names when different bounded contexts use the same word differently.
8. Update tests, documentation, examples, and configuration references.
9. Run tests and static analysis after each safe rename.
10. Avoid large naming churn without design benefit.

## Naming Preference

Favor:

- intent-revealing names
- domain language
- consistent terminology
- searchable symbols
- precise verbs
- cohesive nouns
- positive booleans
- behavior-oriented test names
- role-specific abstractions
- names aligned with ownership

Avoid:

- vague names
- noise words
- overloaded terms
- misleading abstractions
- premature generic names
- implementation leakage in core logic
- synonym drift
- abbreviations without strong convention
- clever names
- names that encode temporary workarounds

## Core Principle

Use naming as a design tool.

A rename is valuable when it reveals domain meaning, clarifies responsibility, exposes boundaries, improves searchability, reduces ambiguity, or makes future change safer without adding unnecessary abstraction.
