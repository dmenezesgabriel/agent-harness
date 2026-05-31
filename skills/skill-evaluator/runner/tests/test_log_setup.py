"""Tests for runner.log_setup — structlog configuration."""

from __future__ import annotations

import io
import json
from collections.abc import Generator

import pytest
import structlog

from runner.log_setup import configure


@pytest.fixture(autouse=True)
def _reset_structlog() -> Generator[None, None, None]:
    """Reset structlog global state after each test to avoid cross-test pollution."""
    yield
    structlog.reset_defaults()


def test_configure_emits_json_with_event_and_fields() -> None:
    stream = io.StringIO()
    configure(stream=stream)

    structlog.get_logger().info("my_event", key="value", count=3)

    record = json.loads(stream.getvalue().strip())
    assert record["event"] == "my_event"
    assert record["key"] == "value"
    assert record["count"] == 3


def test_configure_includes_iso_timestamp() -> None:
    stream = io.StringIO()
    configure(stream=stream)

    structlog.get_logger().info("ts_check")

    record = json.loads(stream.getvalue().strip())
    assert "timestamp" in record
    assert "T" in record["timestamp"]  # ISO 8601 separator


def test_configure_writes_to_provided_stream_not_stderr() -> None:
    stream = io.StringIO()
    configure(stream=stream)

    structlog.get_logger().info("stream_check")

    assert stream.getvalue() != ""


def test_configure_each_event_is_valid_json() -> None:
    stream = io.StringIO()
    configure(stream=stream)
    log = structlog.get_logger()

    log.info("first", x=1)
    log.info("second", x=2)

    lines = [l for l in stream.getvalue().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must not raise
