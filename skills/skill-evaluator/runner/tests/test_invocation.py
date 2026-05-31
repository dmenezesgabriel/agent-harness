from pathlib import Path

from runner.invocation import SkillInvoker
from runner.ports import ArtifactSet


class FakeInvocationAgent:
    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        return ArtifactSet(
            workdir=Path("run"), files={f"{skill_name}.js": f"new Chart(); {prompt}"}
        )


def test_invoke_writes_agent_artifacts_to_generated_dir(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    inputs_dir = evals_dir / "fixtures" / "inputs"
    inputs_dir.mkdir(parents=True)
    (inputs_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

    # Act
    generated_dir = SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert generated_dir == evals_dir / "fixtures" / "_generated_artifacts"
    assert (generated_dir / "dataviz.js").read_text(
        encoding="utf-8"
    ) == "new Chart(); series"


def test_invoke_resets_stale_generated_artifacts(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    generated_dir = evals_dir / "fixtures" / "_generated_artifacts"
    generated_dir.mkdir(parents=True)
    (generated_dir / "stale.txt").write_text("old", encoding="utf-8")
    inputs_dir = evals_dir / "fixtures" / "inputs"
    inputs_dir.mkdir(parents=True)
    (inputs_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

    # Act
    SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert not (generated_dir / "stale.txt").exists()
    assert (generated_dir / ".gitignore").read_text(encoding="utf-8") == "*\n!.gitignore\n"


def test_invoke_returns_golden_dir_when_inputs_dir_is_missing(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    golden_dir = evals_dir / "fixtures" / "golden"
    golden_dir.mkdir(parents=True)

    # Act
    artifacts_dir = SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert artifacts_dir == golden_dir
