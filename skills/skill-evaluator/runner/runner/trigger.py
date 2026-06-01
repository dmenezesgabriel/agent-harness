"""TriggerEvaluator — checks whether an agent routes user messages to a skill correctly.

Reads eval_queries.json (should_trigger / should_not_trigger lists), classifies each
query via a TriggerClassifierPort, and returns a TriggerReport with per-query results
and an overall pass/fail based on accuracy threshold.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import structlog
import yaml

from runner.models import TriggerReport, TriggerResult
from runner.ports import TriggerClassifierPort

_log = structlog.get_logger()

_TRIGGER_PASS_THRESHOLD = 0.7
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def _extract_skill_description(skill_md_path: Path) -> str:
    """Return the description field from a SKILL.md YAML frontmatter block.

    Usage:
        desc = _extract_skill_description(Path('skills/dataviz/SKILL.md'))
    """
    text = skill_md_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return ""
    frontmatter: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    return str(frontmatter.get("description", ""))


class TriggerEvaluator:
    """Evaluate whether a skill is triggered correctly for a set of queries.

    Reads eval_queries.json from evals_dir, classifies each query, and returns
    a TriggerReport. Returns passed=True immediately if no eval_queries.json exists.

    Usage:
        report = TriggerEvaluator().evaluate('dataviz', evals_dir, classifier)
    """

    def evaluate(
        self,
        skill_name: str,
        evals_dir: Path,
        classifier: TriggerClassifierPort,
    ) -> TriggerReport:
        queries_path = evals_dir / "eval_queries.json"
        if not queries_path.exists():
            _log.info("trigger_eval_skipped", skill=skill_name, reason="no eval_queries.json")
            return TriggerReport(results=[], pass_rate=1.0, passed=True)

        raw: dict[str, list[str | dict[str, str]]] = json.loads(queries_path.read_text(encoding="utf-8"))
        description = _extract_skill_description(evals_dir.parent / "SKILL.md")

        results: list[TriggerResult] = []
        for entry in raw.get("should_trigger", []):
            query = entry["query"] if isinstance(entry, dict) else entry
            actual = classifier.classify(description, query)
            results.append(TriggerResult(query=query, expected=True, actual=actual))
            _log.debug("trigger_classified", query=query[:60], expected=True, actual=actual)

        for entry in raw.get("should_not_trigger", []):
            query = entry["query"] if isinstance(entry, dict) else entry
            actual = classifier.classify(description, query)
            results.append(TriggerResult(query=query, expected=False, actual=actual))
            _log.debug("trigger_classified", query=query[:60], expected=False, actual=actual)

        pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 1.0
        passed = pass_rate >= _TRIGGER_PASS_THRESHOLD
        _log.info("trigger_eval_done", skill=skill_name, pass_rate=round(pass_rate, 2), passed=passed)
        return TriggerReport(results=results, pass_rate=pass_rate, passed=passed)
