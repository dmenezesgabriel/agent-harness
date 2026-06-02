@skill_evaluator @golden
Feature: skill-evaluator report validation
  Reports produced by the evaluator must surface the evidence agents need
  to decide whether a skill works and whether it adds value efficiently.

  Background:
    Given the skill-evaluator artifact set is loaded

  Scenario: Valid report exposes core evaluation evidence
    Given the evaluator report "valid_report.md"
    Then the report identifies the evaluated skill and mode
    And the report includes structural checks
    And the report includes skill input size
    And the report includes pass rate

  Scenario: Invalid report fixture demonstrates missing input size detection
    Given the evaluator report "invalid_missing_input_size.md"
    Then the report is missing skill input size
