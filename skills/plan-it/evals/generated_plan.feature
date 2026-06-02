@plan_it @generated
Feature: plan-it generated output validation
  Generated plan-it artifacts must be structured, actionable, and better than
  an unguided plan because they create concrete task files with decision gates.

  Background:
    Given the plan-it artifact set is loaded

  Scenario: Skill produces issue files
    Then the artifact set contains at least one plan issue file
    And the artifact set does not use PLAN_SUMMARY as a substitute
    And the artifact set contains no root-level issue markdown files

  Scenario: Generated issues follow the task contract
    Then every issue file uses the required filename format
    And every issue file has valid task frontmatter
    And every issue file has all required task sections
    And every issue file has no template placeholders
    And every issue file has no empty required sections

  Scenario: Generated issues are actionable
    Then every issue file has stable requirement and acceptance IDs
    And every issue file has AFK or HITL assignability with a reason
    And every issue file has concrete dependencies
    And every issue file has risk-scoped test entries

  Scenario: Architecture work creates ADR stubs
    Then architecture planning output includes an ADR stub when required
    And architecture planning issues link to the ADR dependency

  Scenario: Routine work avoids unnecessary ADRs
    Then routine planning output does not create ADR stubs
