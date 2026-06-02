from __future__ import annotations


class ProviderAbortError(RuntimeError):
    """Abort an evaluation phase when the provider cannot complete a call.

    Usage:
        raise ProviderAbortError("provider rate limit exceeded for judge call")
    """
