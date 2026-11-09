import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from outcome_checks import run_check
from run_outcomes import FIXTURES, Task, arm_prompt, edit_order, load_tasks, main, project_diff, red_first
from run_triggers import prepare_project

TASKS = load_tasks(Path(__file__).parent / "outcomes" / "tasks.json")

CART_FIXES = [("    for item in cart[\"items\"]:", "    for item in cart.get(\"items\", []):"),
              ('len(cart[\"items\"])', 'len(cart.get(\"items\", []))')]
REGRESSION_TEST = '''
class WhenCartIsEmpty(unittest.TestCase):
    def test_empty_cart_checks_out_at_zero(self) -> None:
        self.assertEqual(checkout({})["total_cents"], 0)
'''
PRICING_TESTS = '''import unittest

from src.pricing import line_total_cents, unit_price_cents


class WhenPricingLines(unittest.TestCase):
    def test_tier_edges(self) -> None:
        self.assertEqual([unit_price_cents(100, q) for q in (9, 10, 99, 100)], [100, 90, 90, 80])

    def test_line_total(self) -> None:
        self.assertEqual((line_total_cents(100, 10), line_total_cents(100, 100)), (900, 8000))

    def test_exact_discount_rates(self) -> None:
        self.assertEqual((unit_price_cents(1000, 10), unit_price_cents(1000, 100)), (900, 800))
'''
DISPATCH_NOTIFICATIONS = '''CHANNELS = {"email": lambda u, t: "email:" + u["email"] + ":" + t,
            "sms": lambda u, t: "sms:" + u["phone"] + ":" + t,
            "slack": lambda u, t: "slack:" + u["slack_id"] + ":" + t}


def send(channel: str, user: dict, text: str) -> str:
    if channel not in CHANNELS:
        raise ValueError("unknown channel: " + channel)
    return CHANNELS[channel](user, text)
'''
ELIF_NOTIFICATIONS = '''def send(channel: str, user: dict, text: str) -> str:
    if channel == "email":
        return "email:" + user["email"] + ":" + text
    elif channel == "sms":
        return "sms:" + user["phone"] + ":" + text
    elif channel == "slack":
        return "slack:" + user["slack_id"] + ":" + text
    else:
        raise ValueError("unknown channel: " + channel)
'''


def task(task_id: str) -> Task:
    return next(t for t in TASKS if t.id == task_id)


class Sandbox:
    """A fixtures-only project plus its untouched reference, with helpers an 'agent' edits through."""

    def __enter__(self) -> "Sandbox":
        self._tmp = tempfile.TemporaryDirectory()
        self.project, self.reference = Path(self._tmp.name, "project"), Path(self._tmp.name, "reference")
        for root in (self.project, self.reference):
            root.mkdir()
            prepare_project(root, FIXTURES, with_skills=False)
        return self

    def __exit__(self, *_exc: object) -> None:
        self._tmp.cleanup()

    def write(self, name: str, text: str) -> None:
        (self.project / name).write_text(text)

    def replace(self, name: str, old: str, new: str) -> None:
        self.write(name, (self.project / name).read_text().replace(old, new))

    def append(self, name: str, text: str) -> None:
        self.write(name, (self.project / name).read_text() + text)

    def fix_cart(self) -> None:
        for old, new in CART_FIXES:
            self.replace("src/checkout.py", old, new)

    def checks(self, task_id: str) -> dict[str, bool]:
        return {str(spec["name"]): run_check(spec, self.project, self.reference).passed for spec in task(task_id).checks}


class WhenAnAgentFixesTheCartCrash(unittest.TestCase):
    def test_fix_plus_biting_regression_test_passes_every_check(self) -> None:
        with Sandbox() as box:
            box.fix_cart()
            box.append("tests/test_checkout.py", REGRESSION_TEST)
            self.assertEqual(set(box.checks("cart-crash").values()), {True})

    def test_doing_nothing_fails_the_behavior_and_test_checks(self) -> None:
        with Sandbox() as box:
            result = box.checks("cart-crash")
        self.assertEqual(result, {"suite_passes": True, "hidden_passes": False, "tests_added": False, "tests_fail_on_original": False})

    def test_a_test_that_passes_on_the_bug_is_not_a_regression_test(self) -> None:
        with Sandbox() as box:
            box.fix_cart()
            box.append("tests/test_checkout.py", REGRESSION_TEST.replace("checkout({})", 'checkout({"items": []})'))
            self.assertEqual((box.checks("cart-crash")["tests_added"], box.checks("cart-crash")["tests_fail_on_original"]), (True, False))


class WhenAnAgentAddsTheSlackChannel(unittest.TestCase):
    def test_dispatch_table_passes_behavior_and_branching(self) -> None:
        with Sandbox() as box:
            box.write("src/notifications.py", DISPATCH_NOTIFICATIONS)
            box.append("tests/test_checkout.py", "\nclass WhenSlack(unittest.TestCase):\n    def test_slack(self) -> None:\n        pass\n")
            result = box.checks("slack-channel")
        self.assertEqual((result["hidden_passes"], result["branching_not_increased"]), (True, True))

    def test_another_elif_passes_behavior_but_fails_branching(self) -> None:
        with Sandbox() as box:
            box.write("src/notifications.py", ELIF_NOTIFICATIONS)
            result = box.checks("slack-channel")
        self.assertEqual((result["hidden_passes"], result["branching_not_increased"]), (True, False))


class WhenAnAgentStrengthensHollowTests(unittest.TestCase):
    def test_hollow_baseline_kills_no_mutant_and_keeps_tautologies(self) -> None:
        with Sandbox() as box:
            result = box.checks("hollow-tests")
        self.assertEqual(result, {"suite_passes": True, "no_tautologies": False, "mutants_killed": False})

    def test_real_assertions_kill_the_mutants(self) -> None:
        with Sandbox() as box:
            box.write("tests/test_pricing.py", PRICING_TESTS)
            self.assertEqual(set(box.checks("hollow-tests").values()), {True})


RAISING_INGEST = '''def parse_price(raw: str) -> int:
    return int(raw)


def load_rows(lines: list[str]) -> list[dict]:
    rows = []
    for line in lines:
        sku, price = line.split(",")
        rows.append({"sku": sku, "price_cents": parse_price(price)})
    return rows
'''
LOGGING_INGEST = '''import logging


def load_rows(lines: list[str]) -> list[dict]:
    rows = []
    for line in lines:
        sku, price = line.split(",")
        if not price.isdigit():
            logging.warning("bad price %r", price)
        rows.append({"sku": sku, "price_cents": int(price) if price.isdigit() else 0})
    return rows
'''


class WhenAnAgentMakesIngestFailuresVisible(unittest.TestCase):
    def test_untouched_ingest_fails_behavior_and_swallow_checks(self) -> None:
        with Sandbox() as box:
            result = box.checks("ingest-errors")
        self.assertEqual((result["hidden_passes"], result["no_swallowed_errors"]), (False, False))

    def test_letting_the_error_raise_passes_both(self) -> None:
        with Sandbox() as box:
            box.write("src/ingest.py", RAISING_INGEST)
            result = box.checks("ingest-errors")
        self.assertEqual((result["hidden_passes"], result["no_swallowed_errors"]), (True, True))

    def test_logging_a_warning_also_passes_the_behavior_check(self) -> None:
        with Sandbox() as box:
            box.write("src/ingest.py", LOGGING_INGEST)
            self.assertTrue(box.checks("ingest-errors")["hidden_passes"])


class WhenRunningChecks(unittest.TestCase):
    def test_unknown_check_name_is_a_task_file_bug(self) -> None:
        with Sandbox() as box, self.assertRaisesRegex(ValueError, r"unknown check 'nope'.*suite_passes"):
            run_check({"name": "nope"}, box.project, box.reference)

    def test_router_arm_prefixes_the_slash_command(self) -> None:
        t = task("cart-crash")
        self.assertEqual((arm_prompt(t, "router"), arm_prompt(t, "none")), (f"/engineering-mode {t.prompt}", t.prompt))

    def test_bad_task_entry_names_the_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "t.json")
            path.write_text('[{"id": "x"}]')
            with self.assertRaisesRegex(ValueError, r"each task needs.*'id': 'x'"):
                load_tasks(path)


def transcript(*calls: tuple[str, dict[str, str]]) -> str:
    return json.dumps({"steps": [{"source": "agent", "tool_calls": [{"function_name": n, "arguments": a} for n, a in calls]}]})


class WhenReadingEditOrderFromATranscript(unittest.TestCase):
    def test_shell_heredoc_into_tests_before_an_edit_of_src_is_test_first(self) -> None:
        raw = transcript(("exec", {"command": "cat >> tests/test_checkout.py <<'EOF'\nx\nEOF"}), ("edit", {"file_path": "/w/src/checkout.py"}))
        self.assertEqual(edit_order(raw), "test-first")

    def test_src_edit_before_any_test_write_is_src_first(self) -> None:
        raw = transcript(("edit", {"file_path": "/w/src/checkout.py"}), ("write", {"file_path": "/w/tests/test_new.py"}))
        self.assertEqual(edit_order(raw), "src-first")

    def test_sed_in_place_on_src_counts_as_a_src_write(self) -> None:
        raw = transcript(("exec", {"command": "sed -i 's/a/b/' src/checkout.py"}), ("write", {"file_path": "/w/tests/test_new.py"}))
        self.assertEqual(edit_order(raw), "src-first")

    def test_reads_and_test_runs_are_not_writes(self) -> None:
        look = {"command": "cat src/checkout.py; python3 -m unittest discover -s tests"}
        raw = transcript(("exec", look), ("write", {"file_path": "/w/tests/t.py"}))
        self.assertIsNone(edit_order(raw))

    def test_missing_either_kind_of_edit_is_undetermined(self) -> None:
        self.assertIsNone(edit_order(transcript(("edit", {"file_path": "/w/src/x.py"}))))


def observed(*calls: tuple[str, dict[str, str], str]) -> str:
    """An ATIF export with one step per (tool, arguments, output), each call's output attached by id."""
    steps = [{"source": "agent", "tool_calls": [{"tool_call_id": f"c{i}", "function_name": n, "arguments": a}],
              "observation": {"results": [{"source_call_id": f"c{i}", "content": out}]}}
             for i, (n, a, out) in enumerate(calls)]
    return json.dumps({"steps": steps})


WRITE_TEST = ("write", {"file_path": "/w/tests/test_cart.py"}, "written")
FIX_SRC = ("edit", {"file_path": "/w/src/checkout.py"}, "updated")
RUN_TESTS = {"command": "python3 -m unittest discover -s tests"}


class WhenReadingRedBeforeGreenFromATranscript(unittest.TestCase):
    def test_a_failing_test_run_between_test_and_fix_is_red_first(self) -> None:
        raw = observed(WRITE_TEST, ("exec", RUN_TESTS, "KeyError: 'items'\nFAILED (errors=1)"), FIX_SRC)
        self.assertTrue(red_first(raw))

    def test_a_test_written_first_but_never_run_is_not_red_first(self) -> None:
        self.assertFalse(red_first(observed(WRITE_TEST, FIX_SRC)))

    def test_a_passing_run_before_the_fix_is_not_red_first(self) -> None:
        self.assertFalse(red_first(observed(WRITE_TEST, ("exec", RUN_TESTS, "Ran 4 tests\n\nOK"), FIX_SRC)))

    def test_a_crash_from_a_non_test_command_is_not_red_first(self) -> None:
        repro = ("exec", {"command": "python3 -c 'checkout({})'"}, "Traceback ... KeyError")
        self.assertFalse(red_first(observed(WRITE_TEST, repro, FIX_SRC)))

    def test_a_failing_run_after_the_fix_is_not_red_first(self) -> None:
        self.assertFalse(red_first(observed(WRITE_TEST, FIX_SRC, ("exec", RUN_TESTS, "FAILED (failures=1)"))))

    def test_src_first_is_never_red_first(self) -> None:
        self.assertFalse(red_first(observed(FIX_SRC, ("exec", RUN_TESTS, "FAILED"), WRITE_TEST)))


class WhenDiffingAProject(unittest.TestCase):
    def test_diff_shows_changed_and_added_files_but_not_tooling_dirs(self) -> None:
        with Sandbox() as box:
            box.fix_cart()
            box.write("tests/test_new.py", "x = 1\n")
            (box.project / ".claude").mkdir()
            (box.project / ".claude" / "noise.md").write_text("n")
            diff = project_diff(box.reference, box.project)
        self.assertEqual(("b/src/checkout.py" in diff, "b/tests/test_new.py" in diff, "noise" in diff), (True, True, False))


class WhenRunningMain(unittest.TestCase):
    @staticmethod
    def fake_runner(_model: str, _mode: str, _timeout: int):  # noqa: ANN205 -- returns a Callable matching AgentRunner
        def agent(text: str, project: Path) -> str:
            if "empty cart" in text:
                source = (project / "src" / "checkout.py").read_text()
                for old, new in CART_FIXES:
                    source = source.replace(old, new)
                (project / "src" / "checkout.py").write_text(source)
            call = {"function_name": "skill", "arguments": {"skill": "engineering-mode"}}
            return json.dumps({"steps": [{"source": "agent", "tool_calls": [call]}]})

        return agent

    def run_main(self, keep: Path, *extra: str) -> tuple[int, list[dict[str, object]]]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(["--keep-transcripts", str(keep), "--delay", "0", *extra], self.fake_runner)
        return code, [json.loads(line) for line in out.getvalue().splitlines()]

    def test_runs_every_task_and_arm_and_scores_the_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, rows = self.run_main(Path(tmp), "--runs", "2", "--arms", "none,router")
        self.assertEqual((code, len(rows), {r["runs_ok"] for r in rows}), (0, len(TASKS) * 2, {2}))

    def test_a_fixing_agent_passes_the_behavior_check_and_a_lazy_one_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, rows = self.run_main(Path(tmp), "--runs", "1", "--arms", "none")
        by_task = {str(r["task"]): r["checks"] for r in rows}
        self.assertEqual(by_task["cart-crash"]["hidden_passes"]["passes"], 1)  # type: ignore[index]
        self.assertEqual(by_task["slack-channel"]["hidden_passes"]["passes"], 0)  # type: ignore[index]

    def test_rejects_an_unknown_arm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_main(Path(tmp), "--arms", "bogus")[0], 2)

    def test_scoring_an_empty_directory_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_main(Path(tmp), "--score")[0], 2)


if __name__ == "__main__":
    unittest.main()
