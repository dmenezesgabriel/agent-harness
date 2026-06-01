from pathlib import Path

from runner.invocation import SkillInvoker
from runner.ports import ArtifactSet


class FakeInvocationAgent:
    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        return ArtifactSet(
            workdir=Path("run"), files={f"{skill_name}.js": f"new Chart(); {prompt}"}
        )


class FakeBaselineAgent:
    def invoke_baseline(self, prompt: str) -> ArtifactSet:
        return ArtifactSet(
            workdir=Path("run"), files={"baseline.txt": f"baseline: {prompt}"}
        )


class TestSkillInvoker:
    def test_invoke_writes_agent_artifacts_to_generated_dir(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        inputs_dir = evals_dir / "fixtures" / "inputs"
        inputs_dir.mkdir(parents=True)
        (inputs_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

        # Act
        generated_dir = SkillInvoker().invoke(
            "dataviz", evals_dir, FakeInvocationAgent()
        )

        # Assert
        assert generated_dir == evals_dir / "fixtures" / "_generated_artifacts"
        assert (generated_dir / "dataviz.js").read_text(
            encoding="utf-8"
        ) == "new Chart(); series"

    def test_invoke_resets_stale_generated_artifacts(self, tmp_path: Path) -> None:
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
        assert (generated_dir / ".gitignore").read_text(
            encoding="utf-8"
        ) == "*\n!.gitignore\n"

    def test_invoke_returns_golden_dir_when_inputs_dir_is_missing(
        self,
        tmp_path: Path,
    ) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        golden_dir = evals_dir / "fixtures" / "golden"
        golden_dir.mkdir(parents=True)

        # Act
        artifacts_dir = SkillInvoker().invoke(
            "dataviz", evals_dir, FakeInvocationAgent()
        )

        # Assert
        assert artifacts_dir == golden_dir


class TestSkillInvokerBaseline:
    def test_writes_to_baseline_artifacts_dir(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        inputs_dir = evals_dir / "fixtures" / "inputs"
        inputs_dir.mkdir(parents=True)
        (inputs_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

        # Act
        baseline_dir = SkillInvoker().invoke_baseline(evals_dir, FakeBaselineAgent())

        # Assert
        assert baseline_dir == evals_dir / "fixtures" / "_baseline_artifacts"
        assert (baseline_dir / "baseline.txt").read_text(
            encoding="utf-8"
        ) == "baseline: series"

    def test_resets_stale_baseline_artifacts(self, tmp_path: Path) -> None:
        # Arrange
        evals_dir = tmp_path / "dataviz" / "evals"
        baseline_dir = evals_dir / "fixtures" / "_baseline_artifacts"
        baseline_dir.mkdir(parents=True)
        (baseline_dir / "stale.txt").write_text("old", encoding="utf-8")
        inputs_dir = evals_dir / "fixtures" / "inputs"
        inputs_dir.mkdir(parents=True)
        (inputs_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

        # Act
        SkillInvoker().invoke_baseline(evals_dir, FakeBaselineAgent())

        # Assert
        assert not (baseline_dir / "stale.txt").exists()
        assert (baseline_dir / ".gitignore").read_text(
            encoding="utf-8"
        ) == "*\n!.gitignore\n"
