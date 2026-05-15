# Validation Command Examples

Load this reference only when you need concrete command defaults for a targeted validation run.

Prefer one-off commands for existing tools. Create a script only when the same multi-step logic is repeated often or the command sequence is fragile.

## JavaScript / TypeScript

- targeted tests: `pnpm test -- <pattern>` or `npm test -- <pattern>`
- package test file: `pnpm vitest run path/to/test.ts` or `pnpm jest path/to/test.ts`
- type check: `pnpm typecheck` or `npm run typecheck`
- lint: `pnpm lint` or `npm run lint`
- format check: `pnpm prettier --check .` or `npx prettier --check .`

## Python

- targeted tests: `pytest path/to/test_file.py -k case_name`
- type check: `mypy path/to/module.py`
- lint: `ruff check path/to/module.py`
- format check: `ruff format --check path/to/module.py` or `black --check path/to/module.py`

## Go

- targeted tests: `go test ./path/to/pkg -run TestName`
- broader package tests: `go test ./...`
- vet: `go vet ./...`

## Rust

- targeted tests: `cargo test test_name`
- package tests: `cargo test -p crate_name`
- lint: `cargo clippy --all-targets --all-features -- -D warnings`
- format check: `cargo fmt --check`

## Frontend accessibility and behavior

- targeted component tests: use the project test runner on affected component tests
- browser flow checks: run the smallest relevant Playwright/Cypress spec
- accessibility-focused checks: run the affected behavior tests and verify roles, labels, focus, and keyboard behavior
