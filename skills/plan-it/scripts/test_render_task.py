import json
import shutil
import subprocess  # nosec B404
import tempfile
import unittest
from pathlib import Path
from typing import cast

_SCRIPT = Path(__file__).with_name("render_task.py")


class PlanTaskRendererTest(unittest.TestCase):
    def test_uv_script_renders_valid_task_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            input_path = workspace / "task.json"
            output_path = workspace / "tasks" / "issues" / "001-validate-project.md"
            input_path.write_text(json.dumps(_valid_task()), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertEqual(result.returncode, 0, result.stderr)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# Task: Validate project settings form", content)
            self.assertIn("## Dependencies\n\n- No task dependency", content)
            self.assertIn(
                "- `FR-001`: The project name field rejects empty values.", content
            )
            self.assertIn("### Risk Assessment", content)
            self.assertIn("| Unit Tests | Yes", content)

    def test_uv_script_rejects_placeholder_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            payload = _valid_task()
            functional_requirements = cast(
                list[dict[str, str]], payload["functional_requirements"]
            )
            functional_requirements[0]["text"] = "Implement <missing>."
            input_path = workspace / "task.json"
            output_path = workspace / "tasks" / "issues" / "001-validate-project.md"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unresolved placeholder '<missing>'", result.stderr)
            self.assertFalse(output_path.exists())

    def test_uv_script_rejects_missing_risk_category(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange — omit the Observability Tests entry from the assessment
            payload = _valid_task()
            assessment = payload["required_tests"]
            assert isinstance(assessment, list)
            payload["required_tests"] = [
                c for c in assessment if c.get("heading") != "Observability Tests"
            ]
            input_path = workspace / "task.json"
            output_path = workspace / "tasks" / "issues" / "001-validate-project.md"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing categories", result.stderr)
            self.assertFalse(output_path.exists())

    def test_uv_script_rejects_invalid_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            input_path = workspace / "task.json"
            output_path = workspace / "001-validate-project.md"
            input_path.write_text(json.dumps(_valid_task()), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected tasks/issues/NNN-kebab-slug.md", result.stderr)
            self.assertFalse(output_path.exists())


def _run_renderer(
    input_path: Path, output_path: Path, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return _run_script(
        [
            "--input",
            str(input_path),
            "--output",
            output_path.relative_to(cwd).as_posix(),
        ],
        cwd,
    )


def _run_script(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    uv_path = shutil.which("uv")
    assert uv_path is not None, "uv must be installed to test inline script metadata"
    return subprocess.run(  # nosec B603
        [uv_path, "run", str(_SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _valid_task() -> dict[str, object]:
    return {
        "id": "001",
        "created": "2026-06-02",
        "updated": "2026-06-02",
        "title": "Validate project settings form",
        "priority": "P0 — Required before settings can reject invalid input.",
        "dependencies": [
            "No task dependency; can start after the settings form exists.",
            "No ADR dependency; this task uses existing architecture.",
        ],
        "assignability": {
            "mode": "AFK",
            "reason": "requirements and acceptance criteria are resolved.",
        },
        "context": ["Project owners update names and descriptions from settings."],
        "use_cases": [
            "**Feature**: Project settings validation",
            "**Scenario**: Owner fixes an invalid project name",
            "**Given** Ana is editing project settings",
            "**When** Ana submits an empty project name",
            "**Then** the name field shows a required-field error",
        ],
        "definition_of_ready": ["The existing settings form route is available."],
        "functional_requirements": [
            {"id": "FR-001", "text": "The project name field rejects empty values."}
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-001",
                "text": "Validation keeps the existing successful save flow unchanged.",
            }
        ],
        "observability_requirements": [
            {"id": "OBS-001", "text": "Do not log project names on validation failure."}
        ],
        "acceptance_criteria": [
            {
                "id": "AC-001",
                "text": "**Given** an empty name, **When** Ana submits, **Then** an error appears.",
            }
        ],
        "required_tests": _valid_risk_assessment(),
        "definition_of_done": ["Required tests pass with the project test command."],
    }


def _valid_risk_assessment() -> list[dict[str, object]]:
    return [
        {
            "heading": "Unit Tests",
            "prefix": "UT",
            "risk_present": True,
            "reason": "Isolation risk for name/description length rules",
            "entries": [
                {
                    "id": "UT-001",
                    "text": "Validate name length rules.",
                    "covers": "`FR-001`",
                }
            ],
        },
        {
            "heading": "Integration Tests",
            "prefix": "IT",
            "risk_present": False,
            "reason": "No integration boundary changes",
            "entries": [],
        },
        {
            "heading": "Smoke Tests",
            "prefix": "SMK",
            "risk_present": False,
            "reason": "App startup is unchanged",
            "entries": [],
        },
        {
            "heading": "End-to-End Tests",
            "prefix": "E2E",
            "risk_present": False,
            "reason": "No new critical journey",
            "entries": [],
        },
        {
            "heading": "Regression Tests",
            "prefix": "REG",
            "risk_present": False,
            "reason": "No known previous defect",
            "entries": [],
        },
        {
            "heading": "Performance Tests",
            "prefix": "PT",
            "risk_present": False,
            "reason": "Short string validation only",
            "entries": [],
        },
        {
            "heading": "Security Tests",
            "prefix": "ST",
            "risk_present": False,
            "reason": "No auth or trust-boundary change",
            "entries": [],
        },
        {
            "heading": "Usability Tests",
            "prefix": "UX",
            "risk_present": True,
            "reason": "Error placement and feedback affects UX",
            "entries": [
                {
                    "id": "UX-001",
                    "text": "Verify error placement.",
                    "covers": "`AC-001`",
                }
            ],
        },
        {
            "heading": "Observability Tests",
            "prefix": "OT",
            "risk_present": True,
            "reason": "Sensitive-name logging rule must be verified",
            "entries": [
                {
                    "id": "OT-001",
                    "text": "Verify sensitive names are not logged.",
                    "covers": "`OBS-001`",
                }
            ],
        },
    ]


if __name__ == "__main__":
    unittest.main()
