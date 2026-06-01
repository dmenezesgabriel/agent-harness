@implement_it @golden
Feature: implement-it golden fixture validation
  Structural checks must correctly pass valid implementation summaries
  and flag invalid ones without invoking the skill.

  Background:
    Given the implement-it artifact set is loaded

  Scenario: Valid complete summary has valid YAML frontmatter
    Given the implementation summary "valid_complete_summary.md"
    Then the summary has valid YAML frontmatter

  Scenario: Valid complete summary has all required sections
    Given the implementation summary "valid_complete_summary.md"
    Then the summary has all required sections

  Scenario: Valid complete summary frontmatter has all required fields
    Given the implementation summary "valid_complete_summary.md"
    Then the summary frontmatter has all required fields

  Scenario: Valid complete summary validation run is not empty
    Given the implementation summary "valid_complete_summary.md"
    Then the summary validation run is not empty

  Scenario: Valid minimal summary has all required sections
    Given the implementation summary "valid_minimal_summary.md"
    Then the summary has all required sections

  Scenario: Invalid summary missing sections is flagged
    Given the implementation summary "invalid_missing_sections.md"
    Then the summary is missing required sections

  Scenario: Invalid summary with bad frontmatter is flagged for date format
    Given the implementation summary "invalid_bad_frontmatter.md"
    Then the summary frontmatter has invalid date format

  Scenario: Invalid summary with bad frontmatter is flagged for missing fields
    Given the implementation summary "invalid_bad_frontmatter.md"
    Then the summary frontmatter is missing required fields
