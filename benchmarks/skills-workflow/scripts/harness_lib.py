from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTECTED_PATCH_PATHS = [
    "tests/**",
    "public-results/**",
    "hidden-results/**",
    "outputs/**",
    "prompt-snapshot.json",
    "agent-prompt.md",
    "config-snapshot.json",
    "run-metadata.json",
    "execution-metadata.json",
    "run-summary.json",
    "artifact-summary.json",
    "artifact-schema-validation.json",
    ".git/**",
]


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    repo_dir: Path
    artifacts_dir: Path
    outputs_dir: Path
    public_results_dir: Path
    hidden_results_dir: Path
    trusted_assets_dir: Path
    evaluator_dir: Path
    evaluator_repo_dir: Path
    evaluator_public_results_dir: Path
    evaluator_hidden_results_dir: Path


@dataclass(frozen=True)
class ExecutionOptions:
    pi_bin: str = "pi"
    provider: str | None = None
    model: str | None = None
    thinking: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, data: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _handle_remove_readonly(func: Any, path: str, _: Any) -> None:
    target = Path(path)
    target.chmod(stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
    func(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.rglob("*"), reverse=True):
        mode = stat.S_IWUSR | stat.S_IRUSR
        if child.is_dir():
            mode |= stat.S_IXUSR
        child.chmod(mode)
    path.chmod(stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
    shutil.rmtree(path, onexc=_handle_remove_readonly)


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        remove_tree(dst)
    shutil.copytree(src, dst)


def make_tree_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            path.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        else:
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    root.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def get_trusted_assets_dir(task_workspace: Path, configuration: str, run_name: str = "run-1") -> Path:
    return task_workspace.parent / ".trusted-assets" / task_workspace.name / configuration / run_name


def run_command(command: str, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_test_files(repo_dir: Path) -> list[Path]:
    tests_dir = repo_dir / "tests"
    if not tests_dir.exists():
        return []
    return sorted(path for path in tests_dir.rglob("test_*.py") if path.is_file())


def build_test_asset_manifest(repo_dir: Path) -> dict[str, Any]:
    files = []
    for path in iter_test_files(repo_dir):
        files.append({"path": str(path.relative_to(repo_dir)), "sha256": sha256_file(path)})
    return {"generated_at": utc_now(), "files": files}


def build_schema_validator(schema: dict[str, Any], value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object"]
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")
        for key, subschema in schema.get("properties", {}).items():
            if key in value:
                errors.extend(build_schema_validator(subschema, value[key], f"{path}.{key}"))
    elif schema_type == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array"]
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(build_schema_validator(item_schema, item, f"{path}[{index}]") )
    elif schema_type == "string":
        if not isinstance(value, str):
            return [f"{path}: expected string"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}, got {value!r}")
    return errors


def load_task(task_dir: Path) -> dict[str, Any]:
    task = read_json(task_dir / "task.json")
    task["__task_dir"] = str(task_dir.resolve())
    return task


def get_run_paths(task_workspace: Path, configuration: str, run_name: str = "run-1") -> RunPaths:
    run_dir = task_workspace / configuration / run_name
    evaluator_dir = run_dir / "trusted-eval"
    return RunPaths(
        run_dir=run_dir,
        repo_dir=run_dir / "repo",
        artifacts_dir=run_dir / "artifacts",
        outputs_dir=run_dir / "outputs",
        public_results_dir=run_dir / "public-results",
        hidden_results_dir=run_dir / "hidden-results",
        trusted_assets_dir=get_trusted_assets_dir(task_workspace, configuration, run_name),
        evaluator_dir=evaluator_dir,
        evaluator_repo_dir=evaluator_dir / "repo",
        evaluator_public_results_dir=evaluator_dir / "public-results",
        evaluator_hidden_results_dir=evaluator_dir / "hidden-results",
    )


def get_task_workspace(task: dict[str, Any], task_dir: Path, workspace_root: Path, iteration: str) -> Path:
    default_root = Path(task.get("run", {}).get("workspace_root", str(workspace_root)))
    root = workspace_root if workspace_root != Path(".workspaces/skills-workflow-benchmarks") else default_root
    return root / iteration / task["id"]


def build_config_snapshot(task: dict[str, Any], configuration: str) -> dict[str, Any]:
    return {
        "configuration": configuration,
        "paired": task.get("run", {}).get("paired", False),
        "skill_targets": task.get("skill_targets", []),
        "code_changes_expected": task.get("run", {}).get("code_changes_expected", True),
        "allowed_fix_scope": task.get("run", {}).get("allowed_fix_scope"),
    }


def build_manual_completion_template(task: dict[str, Any], configuration: str) -> dict[str, Any]:
    return {
        "status": "completed",
        "completed_by": "manual",
        "configuration": configuration,
        "summary": "Describe the produced solution or benchmark response.",
        "notes": [
            "Populate required artifacts under artifacts/.",
            "If code changes were made, make them inside repo/ before resuming the harness.",
        ],
        "artifacts_created": [artifact["path"] for artifact in task.get("artifacts", {}).get("required", [])],
    }


def get_skill_paths(task: dict[str, Any]) -> list[str]:
    return [str((Path("skills") / skill).resolve()) for skill in task.get("skill_targets", [])]


def task_has_hidden_checks(task: dict[str, Any]) -> bool:
    return bool(task.get("checks", {}).get("hidden"))


def should_hide_tests(task: dict[str, Any]) -> bool:
    return task_has_hidden_checks(task)


def remove_hidden_tests(repo_dir: Path) -> list[str]:
    removed = []
    tests_dir = repo_dir / "tests"
    if not tests_dir.exists():
        return removed
    for path in sorted(tests_dir.glob("test_hidden_*.py")):
        removed.append(str(path.relative_to(repo_dir)))
        path.unlink()
    return removed


def supports_trusted_patch_evaluation(task: dict[str, Any]) -> bool:
    return True


def build_execution_contract(task: dict[str, Any], configuration: str, paths: RunPaths) -> dict[str, Any]:
    skill_paths = get_skill_paths(task) if configuration == "with_skill" else []
    trusted_manifest_path = (paths.trusted_assets_dir / "test-manifest.json").resolve()
    immutable_paths = [
        "tests/",
        "tests/test_public_*.py",
        "tests/test_hidden_*.py",
        "public-results/",
        "hidden-results/",
        "trusted-eval/",
    ]
    return {
        "mode": "pi_cli",
        "configuration": configuration,
        "prompt_path": str((paths.run_dir / "agent-prompt.md").resolve()),
        "prompt_snapshot_path": str((paths.run_dir / "prompt-snapshot.json").resolve()),
        "skills_enabled": configuration == "with_skill",
        "skill_paths": skill_paths,
        "repo_working_directory": str(paths.repo_dir.resolve()),
        "required_artifacts": [artifact["path"] for artifact in task.get("artifacts", {}).get("required", [])],
        "completion_detection": {
            "primary": "agent process exit + synthesized outputs/completion.json",
            "manual_fallback": "outputs/completion.json may still be created manually",
        },
        "immutable_paths": immutable_paths,
        "artifact_locations": {
            "artifacts_dir": str(paths.artifacts_dir.resolve()),
            "outputs_dir": str(paths.outputs_dir.resolve()),
            "public_results_dir": str(paths.public_results_dir.resolve()),
            "hidden_results_dir": str(paths.hidden_results_dir.resolve()),
        },
        "trusted_test_assets": {
            "directory": str(paths.trusted_assets_dir.resolve()),
            "manifest_path": str(trusted_manifest_path),
            "outside_run_workspace": not is_relative_to(paths.trusted_assets_dir, paths.run_dir),
            "writable_by_owner": os.access(paths.trusted_assets_dir, os.W_OK) if paths.trusted_assets_dir.exists() else None,
        },
        "evaluation_model": {
            "kind": "trusted_patch_evaluation" if supports_trusted_patch_evaluation(task) else "in_workspace_restore",
            "agent_workspace_has_hidden_tests": False if should_hide_tests(task) else True,
            "trusted_evaluator_workspace": str(paths.evaluator_dir.resolve()),
            "protected_patch_paths": PROTECTED_PATCH_PATHS,
        },
    }


def summarize_schema(schema: dict[str, Any]) -> str:
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    parts = []
    if required:
        parts.append("required keys: " + ", ".join(required))
    property_parts = []
    for key in required:
        property_schema = properties.get(key, {})
        property_type = property_schema.get("type", "any")
        details = f"{key} ({property_type}"
        if "enum" in property_schema:
            details += f", enum: {', '.join(map(str, property_schema['enum']))}"
        details += ")"
        property_parts.append(details)
    if property_parts:
        parts.append("expected fields: " + "; ".join(property_parts))
    return ". ".join(parts) if parts else "Must be valid JSON matching the declared schema."


def build_artifact_contract_text(task: dict[str, Any]) -> str:
    contracts = task.get("prompt", {}).get("artifact_contracts", {})
    sections = []
    for artifact in task.get("artifacts", {}).get("required", []):
        path = artifact["path"]
        contract = contracts.get(path, {})
        lines = [f"### {path}"]
        if contract.get("purpose"):
            lines.append(f"- Purpose: {contract['purpose']}")
        if artifact.get("schema"):
            schema = read_json(Path(artifact["schema"]))
            lines.append(f"- Schema summary: {summarize_schema(schema)}")
        if contract.get("instructions"):
            for instruction in contract["instructions"]:
                lines.append(f"- {instruction}")
        if contract.get("example"):
            lines.append("- Example shape:")
            lines.append("```json")
            lines.append(json.dumps(contract["example"], indent=2))
            lines.append("```")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) or "No required artifacts."


def build_agent_prompt(task: dict[str, Any], configuration: str, paths: RunPaths) -> str:
    repo_context = "\n".join(f"- {item}" for item in task.get("prompt", {}).get("repo_context", [])) or "- None provided"
    success_criteria = "\n".join(f"- {item}" for item in task.get("success_criteria", [])) or "- None provided"
    required_artifacts_list = task.get("artifacts", {}).get("required", [])
    required_artifacts = "\n".join(
        f"- {artifact['path']}" for artifact in required_artifacts_list
    ) or "- None required"
    exact_artifact_paths = "\n".join(
        f"- {artifact['path']} -> {str((paths.run_dir / artifact['path']).resolve())}" for artifact in required_artifacts_list
    ) or "- None required"
    artifact_contracts = build_artifact_contract_text(task)
    skill_mode = "Skills enabled" if configuration == "with_skill" else "Skills disabled"
    hidden_test_note = (
        "- Hidden tests are not present in your workspace. The harness will capture your patch and grade it in a separate trusted workspace.\n"
        if should_hide_tests(task)
        else ""
    )
    immutable_asset_rules = """## Non-editable benchmark-owned assets (highest priority)
- Do not edit, rename, delete, replace, or reformat benchmark-owned checks or harness assets.
- In particular, do not modify `tests/`, including `tests/test_public_*.py` and any hidden tests that may exist only in trusted evaluation.
- Do not modify hidden checks, benchmark fixtures, manifests, or validation assets copied/managed by the harness.
- Forbidden examples: changing assertions in public tests, deleting a failing test, updating fixture/check data to make tests pass, or editing files under `public-results/` or `hidden-results/`.
- Treat benchmark-owned tests/check assets as immutable inputs. Fix the application code or produce the required artifact files instead.
- Modifying benchmark-owned assets causes an integrity failure even if the resulting tests pass.
"""
    return f"""# Benchmark task: {task['title']}

Configuration: {configuration}
Skill mode: {skill_mode}
Task id: {task['id']}

{immutable_asset_rules}

## User request
{task.get('prompt', {}).get('user_request', '')}

## Repo context to inspect first
{repo_context}

## Success criteria
{success_criteria}

## Required benchmark artifacts
{required_artifacts}

## Exact artifact output paths for this run
{exact_artifact_paths}

Produce every listed artifact before exit. Treat those exact run-level paths as the only valid destinations for required benchmark artifacts. A run still fails if code/tests pass but any required artifact is missing, written to a different artifacts directory, invalid JSON, or does not satisfy its schema.

## Artifact file contracts
{artifact_contracts}

## Execution contract
- Work only inside this prepared benchmark workspace.
- Make any code changes inside the current working directory repository.
- Write required benchmark artifacts to the exact run-level paths listed above. For this run, that means the absolute paths shown in the "Exact artifact output paths for this run" section under `{paths.artifacts_dir}`, not similarly named paths inside the repo.
- If you create `artifacts/` inside the repo or write copies elsewhere, the run still fails; only the listed run-level artifact files are accepted.
- Benchmark-owned tests/check assets are immutable; never edit repo `tests/` files or harness-managed validation assets.
- When you finish, ensure artifacts are saved and leave the repository in its final state for validation.
- Do not ask for manual benchmark completion files; the harness will synthesize completion metadata automatically.
- If no code changes are expected, avoid modifying repo files outside `artifacts/` unless strictly required by the task.
{hidden_test_note}
## Notes
- Benchmark outputs directory: `{paths.outputs_dir}`
- Public checks will be run after the agent exits.
- Hidden checks will be run after the public checks.
"""


def git_init_baseline(repo_dir: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "benchmark@example.com"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Skills Workflow Benchmark"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=repo_dir, check=True, capture_output=True, text=True)


def capture_submission_patch(paths: RunPaths) -> dict[str, Any]:
    patch_path = paths.outputs_dir / "submission.patch"
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--"],
        cwd=paths.repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    patch_path.write_text(diff.stdout)
    status = subprocess.run(["git", "status", "--short"], cwd=paths.repo_dir, capture_output=True, text=True, check=True)
    summary = {
        "patch_path": str(patch_path.resolve()),
        "bytes": len(diff.stdout.encode()),
        "has_changes": bool(diff.stdout.strip()),
        "git_status": status.stdout.splitlines(),
        "captured_at": utc_now(),
    }
    write_json(paths.outputs_dir / "submission-diff.json", summary)
    return summary


def parse_patch_paths(patch_text: str) -> list[str]:
    touched = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            candidate = line[6:].strip()
            if candidate != "/dev/null":
                touched.append(candidate)
    return sorted(set(touched))


def is_protected_patch_path(path: str) -> bool:
    normalized = path.rstrip("/")
    for pattern in PROTECTED_PATCH_PATHS:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(f"{normalized}/", pattern):
            return True
    return False


def filter_submission_patch(paths: RunPaths) -> dict[str, Any]:
    patch_path = paths.outputs_dir / "submission.patch"
    patch_text = patch_path.read_text() if patch_path.exists() else ""
    touched_paths = parse_patch_paths(patch_text)
    blocked_paths = [path for path in touched_paths if is_protected_patch_path(path)]
    result = {
        "checked_at": utc_now(),
        "patch_path": str(patch_path.resolve()),
        "touched_paths": touched_paths,
        "protected_globs": PROTECTED_PATCH_PATHS,
        "blocked_paths": blocked_paths,
        "accepted": not blocked_paths,
    }
    write_json(paths.outputs_dir / "protected-paths.json", result)
    return result


def initialize_run(
    task_dir: Path,
    task: dict[str, Any],
    task_workspace: Path,
    configuration: str,
    run_name: str = "run-1",
) -> dict[str, Any]:
    paths = get_run_paths(task_workspace, configuration, run_name)
    fixture_src = Path(task["fixture"]["source"])

    if paths.run_dir.exists():
        remove_tree(paths.run_dir)
    if paths.trusted_assets_dir.exists():
        remove_tree(paths.trusted_assets_dir)

    copytree(fixture_src, paths.repo_dir)
    hidden_tests_removed = remove_hidden_tests(paths.repo_dir) if should_hide_tests(task) else []
    copytree(fixture_src, paths.evaluator_repo_dir)
    copytree(fixture_src / "tests", paths.trusted_assets_dir / "tests")
    for directory in [
        paths.artifacts_dir,
        paths.outputs_dir,
        paths.public_results_dir,
        paths.hidden_results_dir,
        paths.evaluator_public_results_dir,
        paths.evaluator_hidden_results_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    write_json(paths.trusted_assets_dir / "test-manifest.json", build_test_asset_manifest(paths.evaluator_repo_dir))
    make_tree_read_only(paths.trusted_assets_dir)
    git_init_baseline(paths.repo_dir)

    trusted_eval_metadata = {
        "model": "trusted_patch_evaluation" if supports_trusted_patch_evaluation(task) else "in_workspace_restore",
        "created_at": utc_now(),
        "workspace": str(paths.evaluator_dir.resolve()),
        "repo_dir": str(paths.evaluator_repo_dir.resolve()),
        "public_results_dir": str(paths.evaluator_public_results_dir.resolve()),
        "hidden_results_dir": str(paths.evaluator_hidden_results_dir.resolve()),
        "hidden_tests_only_in_trusted_workspace": should_hide_tests(task),
        "agent_hidden_tests_removed": hidden_tests_removed,
    }
    write_json(paths.evaluator_dir / "metadata.json", trusted_eval_metadata)
    write_json(paths.run_dir / "prompt-snapshot.json", task.get("prompt", {}))
    write_json(paths.run_dir / "config-snapshot.json", build_config_snapshot(task, configuration))
    (paths.run_dir / "agent-prompt.md").write_text(build_agent_prompt(task, configuration, paths))

    metadata = {
        "task_id": task["id"],
        "configuration": configuration,
        "status": "awaiting_execution",
        "created_at": utc_now(),
        "workspace": str(paths.run_dir),
        "repo_dir": str(paths.repo_dir),
        "artifacts_dir": str(paths.artifacts_dir),
        "outputs_dir": str(paths.outputs_dir),
        "public_results_dir": str(paths.public_results_dir),
        "hidden_results_dir": str(paths.hidden_results_dir),
        "trusted_evaluator_dir": str(paths.evaluator_dir),
        "completion_contract": build_execution_contract(task, configuration, paths),
    }
    write_json(paths.run_dir / "run-metadata.json", metadata)
    write_json(paths.outputs_dir / "completion.template.json", build_manual_completion_template(task, configuration))
    (paths.outputs_dir / "manual-instructions.md").write_text(
        "# Manual benchmark completion fallback\n\n"
        "Automatic Pi execution is the primary flow.\n\n"
        "Benchmark-owned tests/check assets are immutable: do not edit `repo/tests/`, hidden checks, manifests, or harness-managed validation assets.\n\n"
        "If you need to complete the run manually:\n"
        "1. Make any repo changes inside `repo/`, excluding immutable benchmark-owned test/check assets.\n"
        "2. Create the required artifacts under `artifacts/`.\n"
        "3. Copy `outputs/completion.template.json` to `outputs/completion.json` and fill it in.\n"
        "4. Re-run the task harness with `--manual-only` to execute checks and finalize results.\n"
    )
    return metadata


def execute_run(task: dict[str, Any], run_dir: Path, options: ExecutionOptions) -> dict[str, Any]:
    metadata_path = run_dir / "run-metadata.json"
    metadata = read_json(metadata_path)
    paths = get_run_paths(run_dir.parent.parent, metadata["configuration"], run_dir.name)
    contract = metadata["completion_contract"]
    prompt_path = Path(contract["prompt_path"])
    session_dir = (run_dir / "pi-session").resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    command = [options.pi_bin, "--print", "--session-dir", str(session_dir), "--no-extensions", "--no-context-files"]
    if options.provider:
        command.extend(["--provider", options.provider])
    if options.model:
        command.extend(["--model", options.model])
    if options.thinking:
        command.extend(["--thinking", options.thinking])

    if metadata["configuration"] == "with_skill":
        command.append("--no-skills")
        for skill_path in contract.get("skill_paths", []):
            command.extend(["--skill", skill_path])
    else:
        command.append("--no-skills")

    command.append(f"@{prompt_path}")
    started_at = utc_now()
    completed = subprocess.run(command, cwd=paths.repo_dir, capture_output=True, text=True)
    finished_at = utc_now()

    stdout_path = (paths.outputs_dir / "pi-stdout.txt").resolve()
    stderr_path = (paths.outputs_dir / "pi-stderr.txt").resolve()
    stdout_path.write_text(completed.stdout)
    stderr_path.write_text(completed.stderr)

    session_files = sorted(str(path) for path in session_dir.glob("**/*") if path.is_file())
    submission_patch = capture_submission_patch(paths)
    protected_paths = filter_submission_patch(paths)
    execution = {
        "started_at": started_at,
        "finished_at": finished_at,
        "command": command,
        "cwd": str(paths.repo_dir),
        "returncode": completed.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "session_dir": str(session_dir),
        "session_files": session_files,
        "skills_enabled": contract.get("skills_enabled", False),
        "skill_paths": contract.get("skill_paths", []),
        "submission_patch": submission_patch,
        "protected_paths": protected_paths,
    }
    write_json(run_dir / "execution-metadata.json", execution)

    completion_path = paths.outputs_dir / "completion.json"
    existing_completion = read_json(completion_path) if completion_path.exists() else None
    if existing_completion is None or existing_completion.get("completed_by") == "pi_harness":
        completion_payload = {
            "status": "completed" if completed.returncode == 0 else "agent_failed",
            "completed_by": "pi_harness",
            "configuration": metadata["configuration"],
            "summary": "Automatic completion synthesized from Pi execution.",
            "artifacts_created": [artifact["path"] for artifact in task.get("artifacts", {}).get("required", []) if (run_dir / artifact["path"]).exists()],
            "execution": {
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "session_files": session_files,
            },
        }
        write_json(completion_path, completion_payload)

    metadata["status"] = "awaiting_finalization"
    metadata["last_execution_at"] = finished_at
    metadata["execution_metadata_path"] = str(run_dir / "execution-metadata.json")
    metadata["completion_path"] = str(completion_path)
    write_json(metadata_path, metadata)
    return execution


def validate_required_artifacts(task: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    required = []
    missing = []
    invalid = []
    for artifact in task.get("artifacts", {}).get("required", []):
        artifact_path = run_dir / artifact["path"]
        item = {
            "path": artifact["path"],
            "schema": artifact.get("schema"),
            "exists": artifact_path.exists(),
            "schema_valid": None,
            "errors": [],
        }
        if not artifact_path.exists():
            missing.append(artifact["path"])
        elif artifact.get("schema"):
            schema = read_json(Path(artifact["schema"]))
            try:
                value = read_json(artifact_path)
            except json.JSONDecodeError as exc:
                item["schema_valid"] = False
                item["errors"] = [f"invalid JSON: {exc}"]
            else:
                item["errors"] = build_schema_validator(schema, value)
                item["schema_valid"] = not item["errors"]
            if item["schema_valid"] is False:
                invalid.append(artifact["path"])
        required.append(item)
    summary = {
        "required": required,
        "present_count": sum(1 for item in required if item["exists"]),
        "missing": missing,
        "invalid": invalid,
        "all_present": not missing,
        "all_schema_valid": not invalid,
    }
    write_json(run_dir / "artifact-summary.json", summary)
    write_json(run_dir / "artifact-schema-validation.json", summary)
    return summary


def reset_trusted_evaluator_workspace(task: dict[str, Any], paths: RunPaths) -> None:
    copytree(Path(task["fixture"]["source"]), paths.evaluator_repo_dir)
    git_init_baseline(paths.evaluator_repo_dir)


def project_submission_files(paths: RunPaths, touched_paths: list[str]) -> list[dict[str, Any]]:
    projected = []
    for relative in touched_paths:
        source = paths.repo_dir / relative
        target = paths.evaluator_repo_dir / relative
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            projected.append({"path": relative, "action": "copied"})
        elif target.exists():
            target.unlink()
            projected.append({"path": relative, "action": "deleted"})
        else:
            projected.append({"path": relative, "action": "missing_in_both"})
    return projected


def apply_submission_patch(paths: RunPaths) -> dict[str, Any]:
    patch_path = paths.outputs_dir / "submission.patch"
    filter_result = read_json(paths.outputs_dir / "protected-paths.json")
    if not filter_result["accepted"]:
        result = {
            "applied": False,
            "reason": "protected_paths_rejected",
            "blocked_paths": filter_result["blocked_paths"],
            "patch_path": str(patch_path.resolve()),
            "checked_at": utc_now(),
        }
        write_json(paths.evaluator_dir / "patch-application.json", result)
        return result
    patch_text = patch_path.read_text() if patch_path.exists() else ""
    if not patch_text.strip():
        result = {
            "applied": True,
            "reason": "empty_patch",
            "patch_path": str(patch_path.resolve()),
            "mode": "git_apply",
            "checked_at": utc_now(),
        }
        write_json(paths.evaluator_dir / "patch-application.json", result)
        return result

    check = subprocess.run(
        ["git", "apply", "--check", "--binary", str(patch_path.resolve())],
        cwd=paths.evaluator_repo_dir,
        capture_output=True,
        text=True,
    )
    if check.returncode == 0:
        apply = subprocess.run(
            ["git", "apply", "--binary", str(patch_path.resolve())],
            cwd=paths.evaluator_repo_dir,
            capture_output=True,
            text=True,
        )
        result = {
            "applied": apply.returncode == 0,
            "patch_path": str(patch_path.resolve()),
            "mode": "git_apply",
            "touched_paths": filter_result["touched_paths"],
            "git_apply_check": {
                "returncode": check.returncode,
                "stdout": check.stdout,
                "stderr": check.stderr,
            },
            "git_apply": {
                "returncode": apply.returncode,
                "stdout": apply.stdout,
                "stderr": apply.stderr,
            },
            "checked_at": utc_now(),
        }
        write_json(paths.evaluator_dir / "patch-application.json", result)
        return result

    projected = project_submission_files(paths, filter_result["touched_paths"])
    result = {
        "applied": True,
        "patch_path": str(patch_path.resolve()),
        "mode": "file_projection_fallback",
        "touched_paths": filter_result["touched_paths"],
        "projected_changes": projected,
        "git_apply_check": {
            "returncode": check.returncode,
            "stdout": check.stdout,
            "stderr": check.stderr,
        },
        "checked_at": utc_now(),
    }
    write_json(paths.evaluator_dir / "patch-application.json", result)
    return result


def run_checks(task: dict[str, Any], run_dir: Path, phase: str) -> dict[str, Any]:
    raw_commands = task.get("checks", {}).get(phase, [])
    metadata = read_json(run_dir / "run-metadata.json")
    paths = get_run_paths(run_dir.parent.parent, metadata["configuration"], run_dir.name)
    commands = [
        command.format(
            task_dir=task.get("__task_dir", ""),
            run_dir=str(run_dir.resolve()),
            repo_dir=str(paths.repo_dir.resolve()),
            artifacts_dir=str(paths.artifacts_dir.resolve()),
            phase=phase,
        )
        for command in raw_commands
    ]

    if supports_trusted_patch_evaluation(task):
        reset_trusted_evaluator_workspace(task, paths)
        patch_application = apply_submission_patch(paths)
        target_repo_dir = paths.evaluator_repo_dir
        integrity = {
            "phase": phase,
            "evaluation_model": "trusted_patch_evaluation",
            "trusted_assets_dir": str(paths.trusted_assets_dir.resolve()),
            "trusted_evaluator_dir": str(paths.evaluator_dir.resolve()),
            "hidden_tests_only_in_trusted_workspace": should_hide_tests(task),
            "patch_application": patch_application,
            "clean": patch_application["applied"],
            "checked_at": utc_now(),
        }
        out_dir = paths.evaluator_public_results_dir if phase == "public" else paths.evaluator_hidden_results_dir
        write_json(out_dir / "asset-integrity.json", integrity)
    else:
        target_repo_dir = run_dir / "repo"
        integrity = verify_and_restore_test_assets(run_dir, phase)
        out_dir = run_dir / ("public-results" if phase == "public" else "hidden-results")

    results = [run_command(command, target_repo_dir) for command in commands] if integrity["clean"] else []
    summary = {
        "task_id": task["id"],
        "phase": phase,
        "passed": (all(r["passed"] for r in results) if results else True) and integrity["clean"],
        "results": results,
        "asset_integrity": integrity,
        "completed_at": utc_now(),
        "evaluation_workspace": str(target_repo_dir),
    }
    write_json(out_dir / "results.json", summary)
    mirror_dir = run_dir / ("public-results" if phase == "public" else "hidden-results")
    write_json(mirror_dir / "results.json", summary)
    write_json(mirror_dir / "asset-integrity.json", integrity)
    return summary


def verify_and_restore_test_assets(run_dir: Path, phase: str) -> dict[str, Any]:
    repo_dir = run_dir / "repo"
    metadata = read_json(run_dir / "run-metadata.json")
    trusted_assets_dir = Path(metadata["completion_contract"]["trusted_test_assets"]["directory"])
    manifest = read_json(trusted_assets_dir / "test-manifest.json")
    tampered = []
    restored = []
    missing = []
    for item in manifest.get("files", []):
        relative_path = Path(item["path"])
        repo_path = repo_dir / relative_path
        trusted_path = trusted_assets_dir / relative_path
        if not repo_path.exists():
            missing.append(item["path"])
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(trusted_path, repo_path)
            restored.append(item["path"])
            continue
        current_hash = sha256_file(repo_path)
        if current_hash != item["sha256"]:
            tampered.append({"path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": current_hash})
            shutil.copy2(trusted_path, repo_path)
            restored.append(item["path"])
    integrity = {
        "phase": phase,
        "trusted_assets_dir": str(trusted_assets_dir.resolve()),
        "trusted_manifest_path": str((trusted_assets_dir / "test-manifest.json").resolve()),
        "trusted_assets_outside_run_workspace": not is_relative_to(trusted_assets_dir, run_dir),
        "trusted_assets_owner_writable": os.access(trusted_assets_dir, os.W_OK),
        "tampered": tampered,
        "missing": missing,
        "restored": restored,
        "clean": not tampered and not missing,
        "checked_at": utc_now(),
    }
    out_dir = run_dir / ("public-results" if phase == "public" else "hidden-results")
    write_json(out_dir / "asset-integrity.json", integrity)
    return integrity


def finalize_run(task: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    completion_path = run_dir / "outputs" / "completion.json"
    metadata_path = run_dir / "run-metadata.json"
    metadata = read_json(metadata_path)

    if not completion_path.exists():
        metadata["status"] = "awaiting_execution"
        metadata["last_checked_at"] = utc_now()
        write_json(metadata_path, metadata)
        return {"status": "awaiting_execution", "run_dir": str(run_dir)}

    completion = read_json(completion_path)
    if supports_trusted_patch_evaluation(task) and not (run_dir / "outputs" / "submission.patch").exists():
        paths = get_run_paths(run_dir.parent.parent, metadata["configuration"], run_dir.name)
        capture_submission_patch(paths)
        filter_submission_patch(paths)
    artifact_summary = validate_required_artifacts(task, run_dir)
    public_results = run_checks(task, run_dir, "public")
    hidden_results = run_checks(task, run_dir, "hidden")
    execution = read_json(run_dir / "execution-metadata.json") if (run_dir / "execution-metadata.json").exists() else None

    final_status = "completed"
    if execution and execution["returncode"] != 0:
        final_status = "agent_failed"
    elif execution and not execution.get("protected_paths", {}).get("accepted", True):
        final_status = "protected_path_rejected"
    elif not artifact_summary["all_present"]:
        final_status = "artifact_missing"
    elif not artifact_summary["all_schema_valid"]:
        final_status = "artifact_schema_failed"
    elif not public_results["passed"]:
        final_status = "public_failed"
    elif not hidden_results["passed"]:
        final_status = "hidden_failed"

    summary = {
        "task_id": task["id"],
        "configuration": metadata["configuration"],
        "status": final_status,
        "completion": completion,
        "execution": {
            "path": "execution-metadata.json" if execution else None,
            "returncode": None if execution is None else execution["returncode"],
            "session_files": [] if execution is None else execution.get("session_files", []),
            "submission_patch_path": None if execution is None else execution.get("submission_patch", {}).get("patch_path"),
            "protected_paths_path": "outputs/protected-paths.json" if (run_dir / "outputs" / "protected-paths.json").exists() else None,
        },
        "artifacts": artifact_summary,
        "artifact_schema_validation": {
            "passed": artifact_summary["all_schema_valid"],
            "path": "artifact-schema-validation.json",
        },
        "public_results": {
            "passed": public_results["passed"],
            "path": "public-results/results.json",
            "trusted_path": "trusted-eval/public-results/results.json" if supports_trusted_patch_evaluation(task) else None,
        },
        "hidden_results": {
            "passed": hidden_results["passed"],
            "path": "hidden-results/results.json",
            "trusted_path": "trusted-eval/hidden-results/results.json" if supports_trusted_patch_evaluation(task) else None,
        },
        "trusted_evaluation": {
            "enabled": supports_trusted_patch_evaluation(task),
            "workspace": str((run_dir / "trusted-eval").resolve()),
            "metadata_path": "trusted-eval/metadata.json" if (run_dir / "trusted-eval" / "metadata.json").exists() else None,
            "patch_application_path": "trusted-eval/patch-application.json" if (run_dir / "trusted-eval" / "patch-application.json").exists() else None,
        },
        "finalized_at": utc_now(),
    }
    write_json(run_dir / "run-summary.json", summary)

    metadata["status"] = final_status
    metadata["completed_at"] = summary["finalized_at"]
    metadata["completion_path"] = str(completion_path)
    write_json(metadata_path, metadata)
    return summary


def summarize_task_workspace(task: dict[str, Any], task_workspace: Path, run_name: str = "run-1") -> dict[str, Any]:
    configs = task.get("run", {}).get("allowed_configurations", [])
    runs = []
    for configuration in configs:
        run_dir = task_workspace / configuration / run_name
        run_summary_path = run_dir / "run-summary.json"
        metadata_path = run_dir / "run-metadata.json"
        run_summary = read_json(run_summary_path) if run_summary_path.exists() else None
        metadata = read_json(metadata_path) if metadata_path.exists() else None
        runs.append(
            {
                "configuration": configuration,
                "status": (run_summary or metadata or {}).get("status", "missing"),
                "artifact_summary_path": "artifact-summary.json" if (run_dir / "artifact-summary.json").exists() else None,
                "execution_metadata_path": "execution-metadata.json" if (run_dir / "execution-metadata.json").exists() else None,
                "public_passed": None if run_summary is None else run_summary["public_results"]["passed"],
                "hidden_passed": None if run_summary is None else run_summary["hidden_results"]["passed"],
                "artifact_schema_passed": None if run_summary is None else run_summary.get("artifact_schema_validation", {}).get("passed"),
                "trusted_evaluation_enabled": None if run_summary is None else run_summary.get("trusted_evaluation", {}).get("enabled"),
                "run_dir": str(run_dir),
            }
        )
    paired_summary = {
        "task_id": task["id"],
        "paired": task.get("run", {}).get("paired", False),
        "runs": runs,
        "completed_configurations": [run["configuration"] for run in runs if run["status"] not in {"awaiting_execution", "awaiting_finalization"}],
        "all_completed": all(run["status"] not in {"awaiting_execution", "awaiting_finalization"} for run in runs),
        "generated_at": utc_now(),
    }
    write_json(task_workspace / "benchmark-summary.json", paired_summary)
    return paired_summary
