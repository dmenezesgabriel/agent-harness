---
name: prd-it
description: Produces a concise Product Requirements Document (PRD) from a user brief. Captures problem statement, personas, user stories, success metrics, constraints, and explicit non-goals — with no architecture or implementation assumptions. Use when starting a new feature or product where the "what" and "why" need to be defined before design begins — or when the user says "write a PRD", "define the requirements", "what are we building", or "capture the product spec".
compatibility: Designed for Claude Code. Requires bash for script execution.
metadata:
  domain: product-requirements
  version: "1.0"
---

Produce a concise Product Requirements Document for the given feature or product.

Do not include architecture decisions, implementation approach, or technical design.
Do not invent personas, metrics, or constraints not derivable from the brief.

## When NOT to use this skill

- The work is a bug fix, refactor, or single-function change — no PRD needed.
- A task or issue with acceptance criteria already exists — the PRD phase is complete.
- The user already has a written brief or PRD and wants architecture or planning instead.
- The request is exploratory ("how does X work") rather than definitional ("what should X do").
- The scope is a single UI component or utility function with no new user-facing behavior.

## Core workflow

1. If `CONTEXT.md` exists at the project root, read it to load existing domain vocabulary and persona names. Use these consistently throughout the PRD.

2. Classify the request type: `new-product`, `new-feature`, or `behavior-change`. See [prd-rules.md — Request type classification](references/prd-rules.md#request-type-classification). If unclear, ask with numbered alternatives, one marked `(recommended)`.

3. Extract from the brief: problem statement, personas, goals, constraints, and any stated non-goals. Do not ask for information the brief already contains.

4. Identify what is missing. Apply the minimum-viable PRD test from [prd-rules.md — Minimum viable PRD](references/prd-rules.md#minimum-viable-prd). Ask only for what is missing, one question at a time, before writing.

5. Write the PRD using [assets/prd-template.md](assets/prd-template.md) as the exact structure. Apply all rules in [prd-rules.md](references/prd-rules.md).

6. Run `bash scripts/ensure-prd-dir.sh`, then write `docs/prd/<slug>.md`.

7. Update `CONTEXT.md`. If new domain terms, persona names, or product concepts were introduced or clarified, add them using the format in existing entries.

## Output files

```bash
bash scripts/ensure-prd-dir.sh
```

- PRD document: `docs/prd/<slug>.md`

## Before marking complete

- [ ] Problem statement contains no solution language
- [ ] Every success metric is measurable — not "fast", "better", or "improved"
- [ ] At least one explicit non-goal is stated
- [ ] No architecture or implementation details appear in the document
- [ ] Open questions list any scope items that would block design if left unresolved

## Anti-patterns to avoid

**Solution in the problem statement**
- Do not write "we will build X" or "the system should Y" in the problem section. Describe what hurts, not how to fix it.

**Vague success metrics**
- "Improve onboarding" is not a metric. "Reduce time-to-first-action from 8 minutes to under 3 minutes" is.

**Missing non-goals**
- Every PRD must have at least one explicit non-goal. Scope creep starts from unspoken assumptions about what is included.

**Over-specified personas**
- A persona needs a role and a pain point. Do not invent demographics not stated in the brief.

**Architecture in the PRD**
- The PRD defines WHAT and WHY. Technology choices, system structure, and data models belong in the architecture phase, not here.

## Clarification protocol

Ask one question at a time. Each question must include numbered alternatives, one marked `(recommended)`, concrete and mutually exclusive.

Walk decisions in this order: who has the problem → what the problem is → what success looks like → what is out of scope.

Do not ask for information already present in the brief or CONTEXT.md.

## Final response

After creating the file, summarize:

- PRD file created
- Request type classified
- Personas identified
- Success metrics stated
- Non-goals stated
- Open questions, if any
