import json
import shutil
import subprocess  # nosec B404
import tempfile
import unittest
from pathlib import Path
from typing import cast

_SCRIPT = Path(__file__).with_name("render_implementation.py")


class ImplementationRendererTest(unittest.TestCase):
    def test_uv_script_renders_valid_summary_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            input_path = workspace / "summary.json"
            output_path = (
                workspace
                / "tasks"
                / "implementation"
                / "003-age-validator-summary.md"
            )
            input_path.write_text(json.dumps(_valid_summary()), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertEqual(result.returncode, 0, result.stderr)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn(
                "# Implementation Summary: Add AgeValidator Value Object", content
            )
            self.assertIn("## Related Task", content)
            self.assertIn("## Files Changed", content)
            self.assertIn("## Behavior Implemented", content)
            self.assertIn("## Validation Run", content)
            self.assertIn("## Accessibility Notes", content)
            self.assertIn("src/validators/age_validator.py", content)

    def test_uv_script_rejects_placeholder_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            payload = _valid_summary()
            payload["issue"] = "TASK-<missing>"
            input_path = workspace / "summary.json"
            output_path = (
                workspace
                / "tasks"
                / "implementation"
                / "003-age-validator-summary.md"
            )
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unresolved placeholder '<missing>'", result.stderr)
            self.assertFalse(output_path.exists())

    def test_uv_script_rejects_invalid_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            input_path = workspace / "summary.json"
            output_path = workspace / "003-age-validator-summary.md"
            input_path.write_text(json.dumps(_valid_summary()), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "expected tasks/implementation/NNN-kebab-slug-summary.md",
                result.stderr,
            )
            self.assertFalse(output_path.exists())

    def test_uv_script_rejects_missing_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            payload = _valid_summary()
            del payload["title"]
            input_path = workspace / "summary.json"
            output_path = (
                workspace
                / "tasks"
                / "implementation"
                / "003-age-validator-summary.md"
            )
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("title", result.stderr)
            self.assertFalse(output_path.exists())

    def test_uv_script_rejects_empty_files_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)

            # Arrange
            payload = _valid_summary()
            payload["files_changed"] = []
            input_path = workspace / "summary.json"
            output_path = (
                workspace
                / "tasks"
                / "implementation"
                / "003-age-validator-summary.md"
            )
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            # Act
            result = _run_renderer(input_path, output_path, workspace)

            # Assert
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("files_changed", result.stderr)
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


def _valid_summary() -> dict[str, object]:
    return {
        "id": "003",
        "issue": "TASK-003",
        "title": "Add AgeValidator Value Object",
        "created": "2026-06-02",
        "updated": "2026-06-02",
        "related_task": "TASK-003 — Add AgeValidator value object.",
        "files_changed": [
            {
                "path": "src/validators/age_validator.py",
                "reason": "New: AgeValidator value object",
            },
            {
                "path": "tests/unit/validators/test_age_validator.py",
                "reason": "New: 11 unit tests",
            },
        ],
        "behavior": "AgeValidator(age) validates the integer at construction time.",
        "design_notes": "Implemented as a Value Object per OOP calisthenics.",
        "tests": "11 unit tests covering boundary conditions and type rejection.",
        "test_categories_na": [
            "Integration: No external I/O; unit tests cover the full behaviour.",
            "E2E: Single in-memory value object with no API or UI boundary.",
        ],
        "validation_run": "pytest tests/unit/validators/test_age_validator.py -v  "
        "11 passed",
        "accessibility_notes": "N/A — backend module with no UI.",
        "observability_changes": "N/A — validation errors surface as exceptions.",
        "adr_updates": "N/A — no existing ADRs affected.",
        "unresolved_assumptions": "Assumed 120 as the upper bound per AC-2.",
    }


if __name__ == "__main__":
    unittest.main()
