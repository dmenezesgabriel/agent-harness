from __future__ import annotations

import io
import json
import time

import structlog

from runner.strategies._timing import _log_elapsed


def _configure_structlog(stream: io.StringIO) -> None:
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=stream),
    )


class TestLogElapsed:
    def test_log_elapsed_emits_event_skill_and_elapsed(self) -> None:
        stream = io.StringIO()
        _configure_structlog(stream)

        start = time.monotonic() - 1.0
        _log_elapsed("invocation_done", "dataviz", start)

        record = json.loads(stream.getvalue().strip())
        assert record["event"] == "invocation_done"
        assert record["skill"] == "dataviz"
        assert record["elapsed_s"] >= 1.0

    def test_log_elapsed_forwards_extra_kwargs(self) -> None:
        stream = io.StringIO()
        _configure_structlog(stream)

        start = time.monotonic()
        _log_elapsed("judge_phase_done", "dataviz", start, verdicts=3)

        record = json.loads(stream.getvalue().strip())
        assert record["verdicts"] == 3
