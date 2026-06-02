@prd_it @generated
Feature: prd-it generated output validation
  Generated PRDs must define product scope and measurable outcomes without
  leaking architecture or implementation assumptions into the product phase.

  Background:
    Given the prd-it artifact set is loaded

  Scenario: Skill produces a PRD document
    Then the artifact set contains exactly one PRD file

  Scenario: Generated PRD follows the required contract
    Given the generated PRD is loaded
    Then the PRD has valid frontmatter
    And the PRD has all required sections
    And the PRD has no template placeholders

  Scenario: Generated PRD defines product requirements
    Given the generated PRD is loaded
    Then the problem statement has no solution language
    And the PRD includes at least one persona with a pain point
    And the PRD includes measurable success metrics
    And the PRD includes explicit non-goals

  Scenario: Generated PRD stays out of implementation design
    Given the generated PRD is loaded
    Then the PRD contains no architecture or implementation details
