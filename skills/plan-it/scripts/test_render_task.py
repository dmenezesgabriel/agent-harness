import json
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import cast

_SCRIPT = Path(__file__).with_name("render_task.py")


class TestPlanTaskRenderer:
    def test_uv_script_renders_valid_task_markdown(self, tmp_path: Path) -> None:
        input_path = tmp_path / "task.json"
        output_path = tmp_path / "tasks" / "issues" / "001-validate-project.md"
        input_path.write_text(json.dumps(_valid_task()), encoding="utf-8")

        result = _run_renderer(input_path, output_path, tmp_path)

        assert result.returncode == 0, result.stderr
        content = output_path.read_text(encoding="utf-8")
        assert "# Task: Validate project settings form" in content
        assert "## Dependencies\n\n- No task dependency" in content
        assert "- `FR-001`: The project name field rejects empty values." in content
        assert "### Observability Tests" in content

    def test_uv_script_rejects_placeholder_content(self, tmp_path: Path) -> None:
        payload = _valid_task()
        functional_requirements = cast(
            list[dict[str, str]], payload["functional_requirements"]
        )
        functional_requirements[0]["text"] = "Implement <missing>."
        input_path = tmp_path / "task.json"
        output_path = tmp_path / "tasks" / "issues" / "001-validate-project.md"
        input_path.write_text(json.dumps(payload), encoding="utf-8")

        result = _run_renderer(input_path, output_path, tmp_path)

        assert result.returncode != 0
        assert "unresolved placeholder '<missing>'" in result.stderr
        assert not output_path.exists()


def _run_renderer(
    input_path: Path, output_path: Path, cwd: Path
) -> subprocess.CompletedProcess[str]:
    uv_path = shutil.which("uv")
    assert uv_path is not None, "uv must be installed to test inline script metadata"
    return subprocess.run(  # nosec B603
        [
            uv_path,
            "run",
            str(_SCRIPT),
            "--input",
            str(input_path),
            "--output",
            output_path.relative_to(cwd).as_posix(),
        ],
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
        "required_tests": _valid_tests(),
        "definition_of_done": ["Required tests pass with the project test command."],
    }


def _valid_tests() -> dict[str, list[dict[str, str]]]:
    return {
        "unit_tests": [
            {
                "id": "UT-001",
                "text": "Validate name length rules.",
                "covers": "`FR-001`",
            }
        ],
        "integration_tests": [
            _not_applicable("IT-001", "no integration boundary changes")
        ],
        "smoke_tests": [_not_applicable("SMK-001", "app startup is unchanged")],
        "end_to_end_tests": [_not_applicable("E2E-001", "no new critical journey")],
        "regression_tests": [_not_applicable("REG-001", "no known previous defect")],
        "performance_tests": [
            _not_applicable("PT-001", "short string validation only")
        ],
        "security_tests": [
            _not_applicable("ST-001", "no auth or trust-boundary change")
        ],
        "usability_tests": [
            {"id": "UX-001", "text": "Verify error placement.", "covers": "`AC-001`"}
        ],
        "observability_tests": [
            {
                "id": "OT-001",
                "text": "Verify sensitive names are not logged.",
                "covers": "`OBS-001`",
            }
        ],
    }


def _not_applicable(identifier: str, reason: str) -> dict[str, str]:
    return {"id": identifier, "text": f"Not applicable — {reason}."}
