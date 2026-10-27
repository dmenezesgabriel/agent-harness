import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from run_triggers import AgentRunError, load_queries, main, passed, skills_invoked, skills_invoked_atif, trigger_rate


def stream(*skills: str) -> str:
    """Minimal claude stream-json: one assistant tool_use per skill, then a result."""
    lines = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": s}}]}} for s in skills]
    return "\n".join(json.dumps(line) for line in lines + [{"type": "result"}])


def atif(*skills: str) -> str:
    """Minimal devin ATIF export: one agent step per skill tool call."""
    steps = [{"source": "agent", "tool_calls": [{"function_name": "skill", "arguments": {"skill": s}}]} for s in skills]
    return json.dumps({"schema_version": "ATIF-v1.7", "steps": steps})


class FakeAgent:
    """Stands in for the agent CLI: loads the skills mapped to the query text; records the projects it saw."""

    fmt = staticmethod(stream)

    def __init__(self, skills_by_text: dict[str, list[str]], fail_on: str | None = None) -> None:
        self.skills_by_text = skills_by_text
        self.fail_on = fail_on
        self.projects: list[Path] = []

    def __call__(self, text: str, project: Path) -> str:
        self.projects.append(project)
        assert (project / ".claude" / "skills" / "engineering-mode" / "SKILL.md").exists()
        if text == self.fail_on:
            raise AgentRunError("boom")
        return self.fmt(*self.skills_by_text.get(text, []))


class AtifAgent(FakeAgent):
    fmt = staticmethod(atif)


class SkillsInvoked(unittest.TestCase):
    def test_collects_skill_calls_in_order(self) -> None:
        self.assertEqual(skills_invoked(stream("a", "b")), ["a", "b"])

    def test_ignores_other_tools_and_garbage_lines(self) -> None:
        other = json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {}}]}})
        self.assertEqual(skills_invoked(f"not json\n{other}\n{stream('a')}"), ["a"])


class SkillsInvokedAtif(unittest.TestCase):
    def test_collects_skill_calls_in_order(self) -> None:
        self.assertEqual(skills_invoked_atif(atif("a", "b")), ["a", "b"])

    def test_ignores_other_tools_and_non_invoke_calls(self) -> None:
        doc = json.dumps({"steps": [
            {"source": "agent", "tool_calls": [{"function_name": "exec", "arguments": {"skill": "x"}}]},
            {"source": "agent", "tool_calls": [{"function_name": "skill", "arguments": {"mode": "search", "keywords": ["x"]}}]},
            {"source": "agent", "tool_calls": [{"function_name": "skill", "arguments": "{\"skill\": \"c\"}"}]},
        ]})
        self.assertEqual(skills_invoked_atif(doc), ["c"])

    def test_garbage_and_non_dict_return_empty(self) -> None:
        self.assertEqual((skills_invoked_atif("not json"), skills_invoked_atif("[]")), ([], []))


class Rates(unittest.TestCase):
    def test_expected_skill_rate(self) -> None:
        self.assertAlmostEqual(trigger_rate([["a"], ["b"], ["a", "c"]], ("a",)), 2 / 3)

    def test_should_not_trigger_counts_any_skill(self) -> None:
        self.assertAlmostEqual(trigger_rate([[], ["x"], []], ()), 1 / 3)

    def test_no_successful_runs_is_zero(self) -> None:
        self.assertEqual(trigger_rate([], ("a",)), 0.0)

    def test_threshold_is_strict_both_ways(self) -> None:
        self.assertEqual((passed(0.5, ("a",)), passed(0.67, ("a",)), passed(0.5, ()), passed(0.33, ())), (False, True, False, True))


class LoadQueries(unittest.TestCase):
    def test_bad_entry_names_file_and_missing_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "q.json")
            path.write_text('[{"id": "x"}]')
            with self.assertRaisesRegex(ValueError, r"q\.json.*id, query, split, expect.*'query'"):
                load_queries(path)

    def test_shipped_queries_are_balanced_per_split(self) -> None:
        queries = load_queries(Path(__file__).parent / "queries.json")
        shapes = [
            (len(part), sum(bool(q.expect) for q in part))
            for split in ("train", "validation")
            for part in [[q for q in queries if q.split == split]]
        ]
        self.assertEqual(shapes[0], shapes[1])


class Main(unittest.TestCase):
    def run_main(self, agent: FakeAgent, *extra: str) -> tuple[int, list[dict[str, object]]]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "q.json")
            path.write_text(json.dumps([
                {"id": "pos", "query": "design it", "split": "train", "expect": ["principle-x"]},
                {"id": "neg", "query": "rename it", "split": "validation", "expect": []},
            ]))
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main(["--queries", str(path), "--runs", "3", *extra], lambda _model: agent)
        return code, [json.loads(line) for line in out.getvalue().splitlines()]

    def test_exit_0_when_every_query_passes(self) -> None:
        code, results = self.run_main(FakeAgent({"design it": ["principle-x"]}))
        self.assertEqual((code, [r["passed"] for r in results]), (0, [True, True]))

    def test_exit_1_when_expected_skill_never_loads(self) -> None:
        code, results = self.run_main(FakeAgent({}))
        self.assertEqual((code, results[0]["passed"], results[0]["rate"]), (1, False, 0.0))

    def test_split_filter_runs_only_that_split(self) -> None:
        _, results = self.run_main(FakeAgent({}), "--split", "validation")
        self.assertEqual([r["id"] for r in results], ["neg"])

    def test_failed_runs_are_errors_not_silent_misses(self) -> None:
        _, results = self.run_main(FakeAgent({}, fail_on="design it"))
        self.assertEqual((results[0]["errors"], results[0]["runs_ok"], results[0]["passed"]), (3, 0, False))

    def test_each_run_gets_a_fresh_project(self) -> None:
        agent = FakeAgent({})
        self.run_main(agent)
        self.assertEqual(len(set(agent.projects)), len(agent.projects))

    def test_invoke_prefixes_query_and_ignores_the_invoked_skill(self) -> None:
        agent = FakeAgent({"/mode design it": ["mode", "principle-x"], "/mode rename it": ["mode"]})
        code, results = self.run_main(agent, "--invoke", "mode")
        self.assertEqual((code, [r["loaded"] for r in results]), (0, [{"principle-x": 3}, {}]))

    def test_devin_harness_parses_atif_transcripts(self) -> None:
        code, results = self.run_main(AtifAgent({"design it": ["principle-x"]}), "--harness", "devin")
        self.assertEqual((code, [r["loaded"] for r in results]), (0, [{"principle-x": 3}, {}]))

    def test_keep_and_score_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keep, path = Path(tmp, "keep"), Path(tmp, "q.json")
            path.write_text(json.dumps([
                {"id": "pos", "query": "design it", "split": "train", "expect": ["principle-x"]},
                {"id": "miss", "query": "lost it", "split": "train", "expect": ["principle-x"]},
            ]))
            agent = FakeAgent({"design it": ["principle-x"]}, fail_on="lost it")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = main(["--queries", str(path), "--runs", "2", "--keep-transcripts", str(keep)], lambda _m: agent)
            self.assertEqual(code, 1)
            records = [json.loads(l) for l in (keep / "runs.jsonl").read_text().splitlines()]
            self.assertEqual((sum("loaded" in r for r in records), sum("error" in r for r in records)), (2, 2))
            self.assertEqual([p.suffix for p in (keep / "pos").iterdir()], [".jsonl"] * 2)
            self.assertTrue(all(p.name.endswith(".err.txt") for p in (keep / "miss").iterdir()))
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main(["--queries", str(path), "--score-transcripts", str(keep)])
            scored = [json.loads(l) for l in out.getvalue().splitlines()]
            self.assertEqual((code, [r["passed"] for r in scored]), (1, [True, False]))
            self.assertEqual((scored[0]["runs_ok"], scored[0]["ci95"], scored[1]["ci95"]), (2, [0.34, 1.0], [0.0, 0.0]))

    def test_exit_2_on_missing_queries_file(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--queries", "/nonexistent/q.json"]), 2)


if __name__ == "__main__":
    unittest.main()
