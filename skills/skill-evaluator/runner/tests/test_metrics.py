from runner.metrics import CallMetric, CallMetricsCollector


class TestCallMetricsCollector:
    def test_summary_totals_and_groups_by_operation_category(self) -> None:
        # Arrange
        collector = CallMetricsCollector()
        collector.record(CallMetric("invoke:dataviz", 2.0, 100, 30))
        collector.record(CallMetric("judge:r1", 1.5, 200, 40))
        collector.record(CallMetric("judge:r2", 0.5, 50, 40))

        # Act
        summary = collector.summary()

        # Assert
        assert summary.total_calls == 3
        assert summary.total_elapsed_s == 4.0
        assert summary.total_prompt_chars == 350
        assert summary.total_system_chars == 110
        assert summary.elapsed_s_by_operation == {"invoke": 2.0, "judge": 2.0}

    def test_summary_of_empty_collector_is_zeroed(self) -> None:
        summary = CallMetricsCollector().summary()
        assert summary.total_calls == 0
        assert summary.total_elapsed_s == 0.0
        assert summary.elapsed_s_by_operation == {}
