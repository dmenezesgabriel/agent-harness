from __future__ import annotations

import re
import time
from contextlib import suppress
from fnmatch import fnmatch
from pathlib import Path

import structlog
import yaml

from runner.eval_layout import has_ignored_part
from runner.models import (
    GENERATED_ARTIFACTS_PRIMARY,
    ArtifactSelector,
    JudgeReport,
    RubricDefinition,
    RubricFile,
)
from runner.ports import CompareJudgePort, JudgePort

_log = structlog.get_logger()


class RubricJudgeRunner:
    """Evaluate rubric files against golden or live artifacts.

    Usage:
        reports = RubricJudgeRunner().run(evals_dir, artifacts_dir, judge)
    """

    def run(
        self,
        evals_dir: Path,
        artifacts_dir: Path,
        judge: JudgePort,
        generated_only: bool = False,
    ) -> list[JudgeReport]:
        rubrics_dir = evals_dir / "rubrics"
        if not rubrics_dir.exists():
            print("  No rubrics/ directory found - skipping judge")
            return []

        verdicts: list[JudgeReport] = []
        for rubric_file in sorted(rubrics_dir.glob("*.yaml")):
            rubric_file_model = RubricFile.model_validate(
                yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
            )
            for rubric in rubric_file_model.rubrics:
                if (
                    generated_only
                    and rubric.artifact_file != GENERATED_ARTIFACTS_PRIMARY
                ):
                    continue
                artifact_file = _resolve_artifact_file(evals_dir, artifacts_dir, rubric)
                if artifact_file is None:
                    if rubric.artifact_file == GENERATED_ARTIFACTS_PRIMARY:
                        verdicts.append(_missing_generated_artifact_verdict(rubric.id))
                    else:
                        print(
                            f"  Rubric {rubric.id!r}: no matching generated artifact found - skipping"
                        )
                    continue
                if not artifact_file.exists():
                    print(
                        f"  Rubric {rubric.id!r}: fixture {rubric.artifact_file!r} not found - skipping"
                    )
                    continue

                content = artifact_file.read_text(encoding="utf-8")
                if rubric.artifact_section:
                    content = _extract_section(content, rubric.artifact_section)
                _log.info(
                    "judge_start", rubric_id=rubric.id, artifact_chars=len(content)
                )
                t0 = time.monotonic()
                verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
                _log.info(
                    "judge_done",
                    rubric_id=rubric.id,
                    elapsed_s=round(time.monotonic() - t0, 1),
                )
                verdicts.append(verdict)

        self._print_summary(verdicts)
        return verdicts

    def compare_run(
        self,
        evals_dir: Path,
        skill_dir: Path,
        baseline_dir: Path,
        judge: CompareJudgePort,
    ) -> tuple[list[JudgeReport], list[JudgeReport]]:
        """One judge call per generated rubric instead of two.

        Non-generated rubrics (golden fixtures) are judged on skill output only.
        Returns (skill_verdicts, baseline_verdicts).

        Usage:
            skill_v, baseline_v = runner.compare_run(evals_dir, skill_dir, baseline_dir, judge)
        """
        rubrics_dir = evals_dir / "rubrics"
        if not rubrics_dir.exists():
            print("  No rubrics/ directory found - skipping judge")
            return [], []

        skill_verdicts: list[JudgeReport] = []
        baseline_verdicts: list[JudgeReport] = []

        for rubric_file in sorted(rubrics_dir.glob("*.yaml")):
            rubric_file_model = RubricFile.model_validate(
                yaml.safe_load(rubric_file.read_text(encoding="utf-8"))
            )
            for rubric in rubric_file_model.rubrics:
                if rubric.artifact_file == GENERATED_ARTIFACTS_PRIMARY:
                    skill_artifact = _select_generated_artifact(skill_dir, rubric)
                    baseline_artifact = _select_generated_artifact(baseline_dir, rubric)
                    if skill_artifact is None or baseline_artifact is None:
                        skill_verdicts.append(
                            _missing_generated_artifact_verdict(rubric.id)
                        )
                        baseline_verdicts.append(
                            _missing_generated_artifact_verdict(rubric.id)
                        )
                        continue
                    skill_content = skill_artifact.read_text(encoding="utf-8")
                    baseline_content = baseline_artifact.read_text(encoding="utf-8")
                    _log.info(
                        "compare_judge_start",
                        rubric_id=rubric.id,
                        skill_chars=len(skill_content),
                        baseline_chars=len(baseline_content),
                    )
                    t0 = time.monotonic()
                    sv, bv = judge.compare_judge(
                        skill_content,
                        baseline_content,
                        rubric.prompt,
                        rubric_id=rubric.id,
                    )
                    _log.info(
                        "compare_judge_done",
                        rubric_id=rubric.id,
                        elapsed_s=round(time.monotonic() - t0, 1),
                    )
                    skill_verdicts.append(sv)
                    baseline_verdicts.append(bv)
                else:
                    artifact_file = _resolve_artifact_file(evals_dir, skill_dir, rubric)
                    if artifact_file is None or not artifact_file.exists():
                        print(f"  Rubric {rubric.id!r}: fixture not found - skipping")
                        continue
                    content = artifact_file.read_text(encoding="utf-8")
                    if rubric.artifact_section:
                        content = _extract_section(content, rubric.artifact_section)
                    _log.info(
                        "judge_start", rubric_id=rubric.id, artifact_chars=len(content)
                    )
                    t0 = time.monotonic()
                    verdict = judge.judge(content, rubric.prompt, rubric_id=rubric.id)
                    _log.info(
                        "judge_done",
                        rubric_id=rubric.id,
                        elapsed_s=round(time.monotonic() - t0, 1),
                    )
                    skill_verdicts.append(verdict)

        self._print_compare_summary(skill_verdicts, baseline_verdicts)
        return skill_verdicts, baseline_verdicts

    def _print_compare_summary(
        self, skill_verdicts: list[JudgeReport], baseline_verdicts: list[JudgeReport]
    ) -> None:
        skill_passed = sum(1 for v in skill_verdicts if v.passed)
        baseline_passed = sum(1 for v in baseline_verdicts if v.passed)
        print(
            f"\n  Judge: {skill_passed} passed (skill), {baseline_passed} passed (baseline)"
        )
        baseline_by_id = {v.rubric_id: v for v in baseline_verdicts}
        for verdict in skill_verdicts:
            icon = "PASS" if verdict.passed else "FAIL"
            baseline = baseline_by_id.get(verdict.rubric_id)
            if baseline is not None:
                b_icon = "PASS" if baseline.passed else "FAIL"
                print(
                    f"    {icon}/{b_icon} {verdict.rubric_id} "
                    f"(skill={verdict.score:.2f}, baseline={baseline.score:.2f}): {verdict.reasoning}"
                )
            else:
                print(
                    f"    {icon} {verdict.rubric_id} (skill={verdict.score:.2f}): {verdict.reasoning}"
                )

    def _print_summary(self, verdicts: list[JudgeReport]) -> None:
        passed = sum(1 for verdict in verdicts if verdict.passed)
        failed = sum(1 for verdict in verdicts if not verdict.passed)
        print(f"\n  Judge: {passed} passed, {failed} failed")
        for verdict in verdicts:
            icon = "PASS" if verdict.passed else "FAIL"
            print(
                f"    {icon} {verdict.rubric_id} "
                f"(score={verdict.score:.2f}): {verdict.reasoning}"
            )


def _resolve_artifact_file(
    evals_dir: Path, artifacts_dir: Path, rubric: RubricDefinition
) -> Path | None:
    if rubric.artifact_file == GENERATED_ARTIFACTS_PRIMARY:
        return _select_generated_artifact(artifacts_dir, rubric)
    return evals_dir / "fixtures" / "golden" / rubric.artifact_file


def _missing_generated_artifact_verdict(rubric_id: str) -> JudgeReport:
    return JudgeReport(
        rubric_id=rubric_id,
        passed=False,
        score=0.0,
        reasoning="No generated artifact matched the rubric artifact_selector.",
    )


def _select_generated_artifact(
    artifacts_dir: Path, rubric: RubricDefinition
) -> Path | None:
    if rubric.artifact_selector is None:
        return None
    return _select_artifact(artifacts_dir, rubric.artifact_selector)


def _select_artifact(artifacts_dir: Path, selector: ArtifactSelector) -> Path | None:
    """Select the best generated artifact matching explicit rubric criteria.

    Usage:
        _select_artifact(Path("out"), ArtifactSelector(path_patterns=["tasks/issues/*.md"]))
    """
    matches = [
        path
        for path in sorted(artifacts_dir.rglob("*"))
        if _matches_selector(path, artifacts_dir, selector)
    ]
    if not matches:
        return None
    if not selector.prefer_largest:
        return matches[0]
    return max(matches, key=_artifact_size)


def _matches_selector(
    path: Path, artifacts_dir: Path, selector: ArtifactSelector
) -> bool:
    if not path.is_file():
        return False
    relative_path = path.relative_to(artifacts_dir)
    if has_ignored_part(relative_path):
        return False
    if not _matches_extension(path, selector):
        return False
    if not _matches_path_pattern(relative_path, selector):
        return False
    return _matches_content_patterns(path, selector)


def _matches_extension(path: Path, selector: ArtifactSelector) -> bool:
    return not selector.extensions or path.suffix in selector.extensions


def _matches_path_pattern(relative_path: Path, selector: ArtifactSelector) -> bool:
    relative_name = relative_path.as_posix()
    if any(
        fnmatch(relative_name, pattern) for pattern in selector.exclude_path_patterns
    ):
        return False
    if not selector.path_patterns:
        return True
    return any(fnmatch(relative_name, pattern) for pattern in selector.path_patterns)


def _matches_content_patterns(path: Path, selector: ArtifactSelector) -> bool:
    if not selector.content_patterns:
        return True
    with suppress(OSError):
        content = path.read_text(encoding="utf-8", errors="ignore")
        return all(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in selector.content_patterns
        )
    return False


def _artifact_size(path: Path) -> int:
    with suppress(OSError):
        return len(path.read_text(encoding="utf-8", errors="ignore"))
    return -1


def _extract_section(content: str, heading: str) -> str:
    pattern = rf"##\s+{re.escape(heading)}.*?(?=\n##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else content
