# Changelog

All notable changes to this skill kit. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). A skill renamed or removed, or a change to a script's JSON-lines output, is a major change; a new skill or check is minor; wording and fixes are patch.

## [0.1.0] - 2026-11-13

### Added

- 28 skills following the Agent Skills spec. `engineering-mode` routes a feature, bug fix, refactor, or review to the principles and checks; it loads `principle-open-closed` before code adds a case to an existing if/elif chain, switch, or dispatch.
- 20 `principle-*` skills grounded in the books they cite, and `tdd`.
- 6 `find-*` checks (pass-through functions, nested branches, train wrecks, feature envy, swallowed errors, tautological assertions) for Python, TypeScript/JavaScript, Java, and Kotlin.
- Trigger and outcome evals (`evals/triggers/`), with A/B results on devin `swe-2-flash-medium` recorded in the README.

[0.1.0]: https://github.com/dmenezesgabriel/pi-setup/releases/tag/v0.1.0
