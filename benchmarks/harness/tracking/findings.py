"""Structured finding annotations for MLflow runs.

A finding is a human-readable observation that metrics alone can't express:
a failure mode, an anomaly, a qualitative note about agent behavior.

Tag naming convention:
    finding.<category>       — first finding of that category on this run
    finding.<category>.1     — second finding, and so on

This keeps findings grouped alphabetically in the MLflow UI tag table and
filterable via: tags.`finding.<category>` LIKE '%'

The run's Notes section (mlflow.note.content) is also updated when
append_note=True, making the finding visible as a prominent card in the UI.

Usage (inside an active MLflow run):
    log_finding("timeout", "Agent did not respond after 164s")
    log_finding("missing_artifact", "issues-lock.json not created", append_note=True)

Usage (on a completed run by ID):
    log_finding("behave_failure", "Scenario 'Creates the issues directory' failed",
                run_id="abc123def456")

Querying (Python):
    mlflow.search_runs(filter_string="tags.`finding.timeout` LIKE '%'")

Querying (CLI):
    mlflow runs search --filter "tags.`finding.timeout` LIKE '%'"
"""
from __future__ import annotations

import mlflow
from mlflow import MlflowClient

_PREFIX = "finding"
_NOTE_TAG = "mlflow.note.content"


def log_finding(
    category: str,
    message: str,
    run_id: str | None = None,
    append_note: bool = False,
) -> None:
    """Attach a structured finding to a run.

    Args:
        category:    Short dot-free identifier, e.g. "timeout", "missing_artifact",
                     "behave_failure", "missing_file". Becomes the tag key suffix.
        message:     Human-readable description of the finding.
        run_id:      Target run ID. Defaults to the currently active run.
        append_note: Also append to mlflow.note.content (visible Notes card in UI).
    """
    client = MlflowClient()

    if run_id is None:
        active = mlflow.active_run()
        if active is None:
            raise ValueError(
                "log_finding() called with no active MLflow run and no run_id."
            )
        run_id = active.info.run_id

    existing = client.get_run(run_id).data.tags
    key = _unique_key(existing, f"{_PREFIX}.{category}")
    client.set_tag(run_id, key, message)

    if append_note:
        current = existing.get(_NOTE_TAG, "")
        line = f"[{category}] {message}"
        client.set_tag(run_id, _NOTE_TAG, f"{current}\n{line}".lstrip("\n"))


def _unique_key(existing: dict[str, str], base: str) -> str:
    """Return base if unused, else base.1, base.2, …"""
    if base not in existing:
        return base
    n = 1
    while f"{base}.{n}" in existing:
        n += 1
    return f"{base}.{n}"
