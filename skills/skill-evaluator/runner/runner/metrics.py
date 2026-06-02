"""Per-run aggregation of adapter call cost and latency.

Each adapter call already logs its own timing; this collects those calls so a run
can emit a single rollup (call count, total wall-time, total chars) instead of
leaving the operator to sum per-call log lines by hand.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallMetric:
    """One adapter call's measured cost.

    Usage:
        CallMetric(operation="judge:r1", elapsed_s=2.4, prompt_chars=900, system_chars=300)
    """

    operation: str
    elapsed_s: float
    prompt_chars: int
    system_chars: int


@dataclass(frozen=True)
class RunMetricsSummary:
    total_calls: int
    total_elapsed_s: float
    total_prompt_chars: int
    total_system_chars: int
    elapsed_s_by_operation: dict[str, float]


class CallMetricsCollector:
    """Accumulate CallMetric entries across a run and summarize them.

    Injected into adapters so call timing is recorded where it is measured.

    Usage:
        collector = CallMetricsCollector()
        collector.record(CallMetric("judge:r1", 2.4, 900, 300))
        summary = collector.summary()
    """

    def __init__(self) -> None:
        self._metrics: list[CallMetric] = []

    def record(self, metric: CallMetric) -> None:
        self._metrics.append(metric)

    def summary(self) -> RunMetricsSummary:
        return RunMetricsSummary(
            total_calls=len(self._metrics),
            total_elapsed_s=round(sum(m.elapsed_s for m in self._metrics), 1),
            total_prompt_chars=sum(m.prompt_chars for m in self._metrics),
            total_system_chars=sum(m.system_chars for m in self._metrics),
            elapsed_s_by_operation=self._elapsed_by_operation(),
        )

    def _elapsed_by_operation(self) -> dict[str, float]:
        # Group "invoke:dataviz", "judge:r1" by their leading category.
        totals: dict[str, float] = {}
        for metric in self._metrics:
            category = metric.operation.split(":", 1)[0]
            totals[category] = round(totals.get(category, 0.0) + metric.elapsed_s, 1)
        return totals
