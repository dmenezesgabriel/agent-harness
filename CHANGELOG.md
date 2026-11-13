# Changelog

Written by [release-please](https://github.com/googleapis/release-please) from [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) when its release PR is merged; versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). A skill renamed or removed, or a change to a script's JSON-lines output, is breaking (`feat!:` or a `BREAKING CHANGE:` footer; a minor bump while 0.x). A new skill or check is `feat:` (minor). A change to what a skill tells the agent, or a script fix, is `fix:` (patch). `docs:`, `test:`, `build:`, `ci:` and `chore:` do not cut a release.

## v0.1.0 (2026-11-13)

### Features

- 28 skills following the Agent Skills spec. `engineering-mode` routes a feature, bug fix, refactor, or review to the principles and checks; it loads `principle-open-closed` before code adds a case to an existing if/elif chain, switch, or dispatch.
- 20 `principle-*` skills grounded in the books they cite, and `tdd`.
- 6 `find-*` checks (pass-through functions, nested branches, train wrecks, feature envy, swallowed errors, tautological assertions) for Python, TypeScript/JavaScript, Java, and Kotlin.
- Trigger and outcome evals (`evals/triggers/`), with A/B results on devin `swe-2-flash-medium` recorded in the README.
