Feature: plan-it skill produces structured, file-based planning output

  The skill must write issue files to disk, maintain numbering integrity,
  and populate all required sections. These assertions verify observable
  workspace state — not text similarity — so they catch the agent losing
  itself (wrong directory, skipped script, missing section) directly.

  Background:
    Given the agent has run in the workspace

  # ── Directory and file creation ──────────────────────────────────────────

  Scenario: Creates the issues directory
    Then the directory "issues" exists

  Scenario: Writes at least one issue file
    Then at least 1 file matching "issues/*.md" exists

  Scenario: Does not write issue files outside the issues directory
    Then no file matching "*.md" exists at the workspace root

  # ── Issue numbering integrity ─────────────────────────────────────────────

  Scenario: Creates the issues-lock.json counter file
    Then the file "issues-lock.json" exists

  Scenario: Lock file contains a valid next_id integer
    Then "issues-lock.json" is valid JSON
    And "issues-lock.json" has integer key "next_id"
    And "issues-lock.json" key "next_id" is greater than 0

  Scenario: No two issue files share the same numeric prefix
    Then all files in "issues/*.md" have unique numeric prefixes

  Scenario: Issue file names follow 3-digit zero-padded format
    Then every file in "issues/*.md" has a name matching "\d{3}-.+\.md"

  # ── Required section presence ─────────────────────────────────────────────

  Scenario: Every issue file has a non-empty Requirements section
    Then every file in "issues/*.md" contains non-empty section "Requirements"

  Scenario: Every issue file has a non-empty Acceptance Criteria section
    Then every file in "issues/*.md" contains non-empty section "Acceptance Criteria"

  Scenario: Every issue file declares AFK or HITL classification
    Then every file in "issues/*.md" contains any of "AFK,HITL"

  Scenario: Every issue file has a Dependencies section
    Then every file in "issues/*.md" contains non-empty section "Dependencies"

  # ── Content quality ──────────────────────────────────────────────────────────

  Scenario: Every issue file contains at least one properly formatted functional requirement
    Then every file in "issues/*.md" has content matching "FR-\d{3}:"

  Scenario: Every issue file acceptance criteria contain observable Gherkin language
    Then every file in "issues/*.md" contains any of "Given,When,Then"

  Scenario: Every issue file has active status in frontmatter
    Then every file in "issues/*.md" has frontmatter key "status" with value "active"

  Scenario: Every issue file contains test IDs linked to requirement IDs
    Then every file in "issues/*.md" has content matching "Covers (FR|AC|NFR|OBS)-\d{3}"

  # ── ADR stubs (optional but valid when present) ───────────────────────────

  Scenario: If docs/adrs directory exists it contains only .md files
    Then if directory "docs/adrs" exists, it contains only ".md" files

  Scenario: ADR files follow 3-digit zero-padded format
    Then every file in "docs/adrs/*.md" has a name matching "\d{3}-.+\.md"
