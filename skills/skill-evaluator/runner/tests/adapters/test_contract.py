from pathlib import Path

from runner.adapters.contract import (
    ProviderFailureReason,
    build_classify_prompt,
    build_compare_judge_prompt,
    build_judge_prompt,
    classify_token,
    collect_text_artifacts,
    provider_failure_reason,
)


class TestPromptBuilders:
    def test_build_judge_prompt_is_stable(self) -> None:
        assert build_judge_prompt("artifact", "rubric") == (
            "Rubric:\nrubric\n\nArtifact:\nartifact"
        )

    def test_build_compare_judge_prompt_is_stable(self) -> None:
        assert build_compare_judge_prompt("skill", "baseline", "rubric") == (
            "Rubric:\nrubric\n\n"
            "Artifact (Skill):\nskill\n\n"
            "Artifact (Baseline):\nbaseline"
        )

    def test_build_classify_prompt_is_stable(self) -> None:
        assert build_classify_prompt("description", "query") == (
            "Skill description:\ndescription\n\nUser message:\nquery"
        )


class TestClassifyToken:
    def test_classify_token_accepts_invoke_case_insensitively(self) -> None:
        assert classify_token(" invoke\n") is True

    def test_classify_token_rejects_skip(self) -> None:
        assert classify_token("SKIP") is False


class TestArtifactCollection:
    def test_collect_text_artifacts_uses_shared_ignore_policy(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
        (tmp_path / "node_modules" / "x").mkdir(parents=True)
        (tmp_path / "node_modules" / "x" / "index.js").write_text(
            "lib", encoding="utf-8"
        )
        (tmp_path / "references").mkdir()
        (tmp_path / "references" / "rules.md").write_text("rules", encoding="utf-8")

        assert collect_text_artifacts(tmp_path) == {"src/app.py": "print('ok')"}


class TestProviderFailureReason:
    def test_provider_failure_reason_detects_timeout(self) -> None:
        assert provider_failure_reason(TimeoutError("timed out")) == (
            ProviderFailureReason.TIMEOUT
        )

    def test_provider_failure_reason_detects_rate_limit(self) -> None:
        assert provider_failure_reason(RuntimeError("429 rate limit exceeded")) == (
            ProviderFailureReason.RATE_LIMIT
        )
