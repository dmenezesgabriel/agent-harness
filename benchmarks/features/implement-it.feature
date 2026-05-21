Feature: implement-it skill produces working code with a structured summary

  Background:
    Given the agent has run in the workspace

  # ── Directory and file creation ──────────────────────────────────────────

  Scenario: Creates the implementation directory
    Then the directory "implementation" exists

  Scenario: Writes at least one implementation summary file
    Then at least 1 file matching "implementation/*.md" exists

  Scenario: Summary file names follow 3-digit zero-padded format
    Then every file in "implementation/*.md" has a name matching "\d{3}-.+summary\.md"

  # ── Summary content ───────────────────────────────────────────────────────

  Scenario: Every summary has a non-empty files changed section
    Then every file in "implementation/*.md" contains non-empty section "files changed"

  Scenario: Every summary has a non-empty tests section
    Then every file in "implementation/*.md" contains non-empty section "tests"

  Scenario: Every summary documents validations run
    Then every file in "implementation/*.md" contains any of "lint,typecheck,build,test"

  # ── Content quality ──────────────────────────────────────────────────────────

  Scenario: Every summary has a non-empty Design Notes section
    Then every file in "implementation/*.md" contains non-empty section "Design Notes"

  Scenario: Every summary documents ADR update status
    Then every file in "implementation/*.md" contains any of "ADR Updates,Not applicable"

  # ── Code quality ──────────────────────────────────────────────────────────

  Scenario: Agent does not modify files outside task scope
    Then the file "TASK_SCOPE_VIOLATION" does not exist
