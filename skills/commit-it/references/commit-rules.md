# Commit Rules

## Atomicity

One commit = one logical concern. A concern is atomic when:

- It can be described in a single sentence without "and".
- Reverting it leaves the system in a valid, functional state.
- It does not include unrelated file changes.

**Group together:**
- A source change and its tests
- A source change and its generated file (lock file, migration, compiled output)
- A source change and the docs that describe it, when they change together

**Split apart:**
- Unrelated bug fixes
- A refactor and a feature that uses the refactored code
- A dependency bump and the code change that uses it
- A config change and the application change it enables (unless inseparable)

**Order by dependency**: commit the change that others depend on first.

## Message format

```
<type>(<scope>): <description>

[body — optional, 72 chars/line]

[footer — optional]
```

- `type`: see [Type taxonomy](#type-taxonomy)
- `scope`: optional — module, package, or component name in lowercase (e.g. `auth`, `plan-it`)
- `description`: imperative mood, lowercase, no trailing period, ≤72 chars total on first line
- `body`: explain *why*, not *what*; wrap at 72 chars
- `footer`: `BREAKING CHANGE: <description>` or `Closes #NNN`

Good:
- `feat(plan-it): add HITL/AFK classification to task template`
- `fix(review-it): stop marking missing ADR updates as Suggestion`
- `chore: remove deprecated .pi skill symlinks`
- `refactor(harness): extract adapter registry into its own module`

Bad:
- `updated files` — no type, no imperative, vague
- `Fix bug` — capitalized, no type, no description
- `feat: add feature and fix the thing and update docs` — multiple concerns

## Type taxonomy

| Type | Use when |
|------|----------|
| `feat` | New behavior visible to users or callers |
| `fix` | Corrects a defect |
| `refactor` | Restructures code without changing external behavior |
| `test` | Adds or corrects tests only |
| `docs` | Documentation only |
| `chore` | Maintenance: dependency bumps, config, scripts, CI non-pipeline |
| `build` | Build system or tooling changes |
| `ci` | CI/CD pipeline changes |
| `perf` | Performance improvement with no behavior change |
| `revert` | Reverts a previous commit (include reverted hash in body) |
| `style` | Formatting only — no logic change |

When unsure between `refactor` and `chore`: if it touches production source, use `refactor`; if it touches only tooling, config, or scripts, use `chore`.

## Breaking changes

A breaking change alters a public API, contract, or behavior that requires callers to update.

Encode it in the commit footer:

```
feat(api): replace project ID type from int to UUID

BREAKING CHANGE: project IDs are now UUIDs. Clients must update all
stored IDs and API calls that pass integer project IDs.
```

Optionally append `!` after the type for machine-readable signalling: `feat!:` or `feat(api)!:`.

## Scope conventions

Use scope when the repo contains multiple distinct modules and the change is confined to one.

Good scopes for this repo:
- Skill names: `plan-it`, `implement-it`, `review-it`, `commit-it`
- Infrastructure areas: `harness`, `benchmarks`, `scripts`

Omit scope when the change is cross-cutting or the repo is a single module.
