@implement_it @generated
Feature: implement-it generated summary validation
  After the skill is invoked with an input task, the generated output
  must include a properly structured implementation summary.

  Background:
    Given the implement-it artifact set is loaded

  Scenario: Skill produces at least one markdown artifact
    Then the artifact set contains at least one markdown file

  Scenario: Generated summary has valid YAML frontmatter
    Given the generated implementation summary is loaded
    Then the summary has valid YAML frontmatter

  Scenario: Generated summary has all required sections
    Given the generated implementation summary is loaded
    Then the summary has all required sections
