from pathlib import Path

from runner.trigger import TriggerEvaluator, _extract_skill_description


class FakeTriggerClassifier:
    def __init__(self, responses: dict[str, bool]) -> None:
        self._responses = responses

    def classify(self, _skill_description: str, query: str) -> bool:
        return self._responses.get(query, False)


_SHOULD_TRIGGER = ["make a chart", "plot this CSV"]
_SHOULD_NOT_TRIGGER = ["fix my CSS", "run a SQL query"]

_QUERIES_JSON = """{
  "should_trigger": [
    {"query": "make a chart"},
    {"query": "plot this CSV", "note": "csv input"}
  ],
  "should_not_trigger": [
    {"query": "fix my CSS"},
    {"query": "run a SQL query"}
  ]
}"""

_SKILL_MD = """---
name: dataviz
description: >
  Use when the user wants to visualize, chart, or plot data.
---

# dataviz
"""


def _make_evals_dir(tmp_path: Path, queries_json: str | None = _QUERIES_JSON) -> Path:
    skill_dir = tmp_path / "dataviz"
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(_SKILL_MD, encoding="utf-8")
    if queries_json is not None:
        (evals_dir / "eval_queries.json").write_text(queries_json, encoding="utf-8")
    return evals_dir


class TestTriggerEvaluator:
    def test_all_correct_passes(self, tmp_path: Path) -> None:
        evals_dir = _make_evals_dir(tmp_path)
        classifier = FakeTriggerClassifier(
            {
                "make a chart": True,
                "plot this CSV": True,
                "fix my CSS": False,
                "run a SQL query": False,
            }
        )

        report = TriggerEvaluator().evaluate("dataviz", evals_dir, classifier)

        assert report.passed is True
        assert report.pass_rate == 1.0
        assert all(r.passed for r in report.results)

    def test_below_threshold_fails(self, tmp_path: Path) -> None:
        evals_dir = _make_evals_dir(tmp_path)
        # Classifier always returns True — should-trigger pass, should-not-trigger all fail → 2/4 = 0.5
        classifier = FakeTriggerClassifier(
            {
                "make a chart": True,
                "plot this CSV": True,
                "fix my CSS": True,
                "run a SQL query": True,
            }
        )

        report = TriggerEvaluator().evaluate("dataviz", evals_dir, classifier)

        assert report.passed is False
        assert report.pass_rate == 0.5

    def test_skips_when_no_eval_queries_file(self, tmp_path: Path) -> None:
        evals_dir = _make_evals_dir(tmp_path, queries_json=None)
        classifier = FakeTriggerClassifier({})

        report = TriggerEvaluator().evaluate("dataviz", evals_dir, classifier)

        assert report.passed is True
        assert report.results == []


class TestExtractSkillDescription:
    def test_extract_description_parses_yaml_frontmatter(self, tmp_path: Path) -> None:
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(_SKILL_MD, encoding="utf-8")

        description = _extract_skill_description(skill_md)

        assert "visualize" in description
        assert "chart" in description
