"""TriggerEvaluator — checks whether an agent routes user messages to a skill correctly.

Reads eval_queries.json (should_trigger / should_not_trigger lists), classifies each
query via a TriggerClassifierPort, and returns a TriggerReport with per-query results
and an overall pass/fail based on accuracy threshold.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import structlog
import yaml

from runner.models import (
    PASS_THRESHOLD,
    EvalQueriesFile,
    EvalQuery,
    TriggerReport,
    TriggerResult,
)
from runner.ports import TriggerClassifierPort

_log = structlog.get_logger()
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
            _log.info(
                "trigger_eval_skipped", skill=skill_name, reason="no eval_queries.json"
            )
            return TriggerReport(results=[], pass_rate=1.0, passed=True)

        queries = EvalQueriesFile.model_validate_json(
            queries_path.read_text(encoding="utf-8")
        )
        description = _extract_skill_description(evals_dir.parent / "SKILL.md")

        results = _classify_category(
            queries.should_trigger, "should_trigger", True, description, classifier
        )
        results += _classify_category(
            queries.should_not_trigger,
            "should_not_trigger",
            False,
            description,
            classifier,
        )

        pass_rate = (
            sum(1 for r in results if r.passed) / len(results) if results else 1.0
        )
        passed = pass_rate >= PASS_THRESHOLD
        passed_count = sum(1 for r in results if r.passed)
        _log.info(
            "trigger_eval_done",
            skill=skill_name,
            total=len(results),
            passed_count=passed_count,
            pass_rate=round(pass_rate, 2),
            passed=passed,
        )
        return TriggerReport(results=results, pass_rate=pass_rate, passed=passed)


def _classify_category(
    queries: list[EvalQuery],
    category: str,
    expected: bool,
    description: str,
    classifier: TriggerClassifierPort,
) -> list[TriggerResult]:
    """Classify one query category and return its per-query trigger results.

    Usage:
        _classify_category(file.should_trigger, "should_trigger", True, desc, clf)
    """
    results: list[TriggerResult] = []
    for index, entry in enumerate(queries, start=1):
        start = time.monotonic()
        _log.info(
            "trigger_classify_start",
            category=category,
            index=index,
            query_chars=len(entry.query),
        )
        actual = classifier.classify(description, entry.query)
        results.append(
            TriggerResult(query=entry.query, expected=expected, actual=actual)
        )
        _log.info(
            "trigger_classified",
            category=category,
            index=index,
            query=entry.query[:60],
            expected=expected,
            actual=actual,
            elapsed_s=round(time.monotonic() - start, 1),
        )
    return results
