"""Structlog configuration for the skill-evaluator runner.

Emits one-line JSON to stderr so timing events are parseable by log aggregators
without mixing with the plain-text user-facing stdout output.

Usage:
    configure()          # sets up structlog globally; call once in main()
    configure(stream=s)  # redirect to an alternate stream (e.g. for tests)
"""

from __future__ import annotations

import sys
from typing import TextIO

import structlog


def configure(stream: TextIO | None = None) -> None:
    """Configure structlog to emit JSON events with ISO timestamps.

    Args:
        stream: Output destination (default: sys.stderr).
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=stream or sys.stderr),
    )
