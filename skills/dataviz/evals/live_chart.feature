@dataviz @live
Feature: dataviz live skill output validation
  Chart code produced by the dataviz skill on a real invocation must follow
  all design rules. These scenarios run only in invoke mode against live output.

  Background:
    Given the dataviz artifact set is loaded

  Scenario: Skill produces at least one chart artifact
    Then the artifact set contains a chart artifact

  Scenario: Live chart follows all structural rules
    Given the live chart artifact
    Then the chart does not have a non-zero y-axis minimum
    And the chart does not use 3D rendering
    And the chart does not use dual y-axes
    And the chart type is appropriate for its labels
    And the chart has an explicit background color
    And the chart uses at most 7 distinct colors
    And the chart does not use a red-green color pair

  Scenario: Live chart contains no anti-patterns
    Given the live chart artifact
    Then the artifact does not contain 3D keywords
    And the artifact does not contain dual y-axis keywords
