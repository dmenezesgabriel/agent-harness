@implement_it
Feature: implement-it design decision validation
  Design decision checks must correctly pass valid design choices
  and flag invalid ones without invoking the skill.

  Background:
    Given the implement-it artifact set is loaded

  @golden
  Scenario: DIP/Adapter decision is documented in Design Notes
    Given the implementation summary "valid_design_dip_adapter.md"
    Then the design notes name a SOLID principle
    And the design notes reference the "Adapter" pattern
    And the design notes explain WHY the principle was chosen

  @golden
  Scenario: OCP/Strategy decision is documented in Design Notes
    Given the implementation summary "valid_design_ocp_strategy.md"
    Then the design notes name a SOLID principle
    And the design notes reference the "Strategy" pattern
    And the design notes explain WHY the principle was chosen

  @golden
  Scenario: No overengineering when design pressure is absent
    Given the implementation summary "valid_design_no_overengineering.md"
    Then the design notes explicitly justify why no design pattern was needed

  @golden
  Scenario: Invalid design overengineering is flagged
    Given the implementation summary "invalid_design_overengineering.md"
    Then the design notes apply a pattern without a valid reason
