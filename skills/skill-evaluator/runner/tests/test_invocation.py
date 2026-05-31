from pathlib import Path

from runner.invocation import SkillInvoker
from runner.ports import ArtifactSet


class FakeInvocationAgent:
    def invoke_skill(self, skill_name: str, prompt: str) -> ArtifactSet:
        return ArtifactSet(
            workdir=Path("run"), files={f"{skill_name}.js": f"new Chart(); {prompt}"}
        )


def test_invoke_writes_agent_artifacts_to_live_dir(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    fixtures_dir = evals_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)
    (fixtures_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

    # Act
    live_dir = SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert live_dir == fixtures_dir / "_live"
    assert (live_dir / "dataviz.js").read_text(
        encoding="utf-8"
    ) == "new Chart(); series"


def test_invoke_resets_stale_live_artifacts(tmp_path: Path) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    fixtures_dir = evals_dir / "fixtures"
    live_dir = fixtures_dir / "_live"
    live_dir.mkdir(parents=True)
    (live_dir / "stale.txt").write_text("old", encoding="utf-8")
    (fixtures_dir / "input_timeseries.md").write_text("series", encoding="utf-8")

    # Act
    SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert not (live_dir / "stale.txt").exists()
    assert (live_dir / ".gitignore").read_text(encoding="utf-8") == "*\n!.gitignore\n"


def test_invoke_returns_fixtures_dir_when_input_fixture_is_missing(
    tmp_path: Path,
) -> None:
    # Arrange
    evals_dir = tmp_path / "dataviz" / "evals"
    fixtures_dir = evals_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)

    # Act
    artifacts_dir = SkillInvoker().invoke("dataviz", evals_dir, FakeInvocationAgent())

    # Assert
    assert artifacts_dir == fixtures_dir
