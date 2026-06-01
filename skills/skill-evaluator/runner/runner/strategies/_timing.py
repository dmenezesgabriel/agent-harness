from __future__ import annotations

import time

import structlog

_log = structlog.get_logger()


def _log_elapsed(event: str, skill: str, start: float, **extra: object) -> None:
    """Log event with elapsed_s since start. Extra kwargs forwarded to the log entry."""
    _log.info(event, skill=skill, elapsed_s=round(time.monotonic() - start, 1), **extra)
