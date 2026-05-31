@dataviz @golden
Feature: dataviz golden fixture validation
  Detection patterns must correctly pass valid artifacts and flag invalid ones.
  Run against static fixtures — no agent invocation required.

  Background:
    Given the dataviz artifact set is loaded

  # ── valid fixture: all checks must pass ──────────────────────────────────────

  Scenario: Valid bar chart passes zero-baseline check
    Given the chart artifact "valid_bar_chart.js"
    Then the chart does not have a non-zero y-axis minimum

  Scenario: Valid bar chart passes 3D-rendering check
    Given the chart artifact "valid_bar_chart.js"
    Then the chart does not use 3D rendering

  Scenario: Valid bar chart passes dual-axes check
    Given the chart artifact "valid_bar_chart.js"
    Then the chart does not use dual y-axes

  Scenario: Valid bar chart passes color-count check
    Given the chart artifact "valid_bar_chart.js"
    Then the chart uses at most 7 distinct colors

  Scenario: Valid bar chart has an explicit background color
    Given the chart artifact "valid_bar_chart.js"
    Then the chart has an explicit background color

  Scenario: Valid bar chart passes colorblind red-green check
    Given the chart artifact "valid_bar_chart.js"
    Then the chart does not use a red-green color pair

  Scenario: Valid multi-series time-series chart uses a line encoding
    Given the chart artifact "valid_line_timeseries.js"
    Then the chart uses a line type with ISO date labels
    And the chart has at least 4 data series
    And the chart uses at most 7 distinct colors
    And the chart does not use a red-green color pair

  Scenario: Valid dashboard includes narrative, context, and multiple charts
    Given the chart artifact "valid_dashboard.html"
    Then the dashboard has at least 2 chart canvases
    And the artifact includes a narrative takeaway
    And the artifact includes a data source or time period note
    And the chart does not use 3D rendering
    And the chart does not use dual y-axes
    And the chart does not use a red-green color pair

  # ── invalid fixtures: detection patterns must trigger ────────────────────────

  Scenario: Truncated bar chart is flagged for non-zero y-minimum
    Given the chart artifact "invalid_truncated_bar.js"
    Then the chart has a non-zero y-axis minimum

  Scenario: Bar chart with ISO date labels is flagged
    Given the chart artifact "invalid_bar_timeseries.js"
    Then the chart has a bar type with ISO date labels

  Scenario: Pie chart with 6 slices is flagged
    Given the chart artifact "invalid_pie_6slices.js"
    Then the pie chart exceeds 5 slices

  Scenario: Chart with 8 colors is flagged
    Given the chart artifact "invalid_many_colors.js"
    Then the chart exceeds 7 background colors

  Scenario: Chart with red-green pair is flagged for colorblind failure
    Given the chart artifact "invalid_red_green.js"
    Then the chart has a red-green color pair
