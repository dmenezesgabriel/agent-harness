# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import argparse
import base64
import json
import logging
import mimetypes
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")


TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".yaml", ".yml", ".xml", ".html", ".css", ".sh", ".rb", ".go", ".rs",
    ".java", ".c", ".cpp", ".h", ".hpp", ".sql", ".r", ".toml",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

MIME_OVERRIDES = {
    ".svg": "image/svg+xml",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "inputs"}

VIEWER_PLACEHOLDER = "/*__EMBEDDED_DATA__*/"


def get_mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME_OVERRIDES:
        return MIME_OVERRIDES[ext]
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


def discover_runs(root: Path) -> list[dict]:
    runs = []
    for path in root.iterdir():
        if not path.is_dir() or path.name in SKIP_DIRS:
            continue
        outputs_dir = path / "outputs"
        if outputs_dir.is_dir():
            run = build_run(root, path)
            if run:
                runs.append(run)
        else:
            runs.extend(discover_runs(path))
    runs.sort(key=lambda r: (r.get("eval_id", float("inf")), r["id"]))
    return runs


def find_metadata(run_dir: Path) -> dict | None:
    for parent in [run_dir, *run_dir.parents]:
        candidate = parent / "eval_metadata.json"
        text = read_text(candidate)
        if text is None:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return None


def extract_prompt(run_dir: Path) -> str:
    metadata = find_metadata(run_dir)
    if metadata:
        prompt = metadata.get("prompt", "")
        if prompt:
            return prompt

    for candidate in [run_dir / "transcript.md", run_dir / "outputs" / "transcript.md"]:
        text = read_text(candidate)
        if text is None:
            continue
        match = re.search(r"## Eval Prompt\n\n([\s\S]*?)(?=\n##|$)", text)
        if match:
            return match.group(1).strip()

    return "(No prompt found)"


def extract_eval_id(run_dir: Path) -> object:
    metadata = find_metadata(run_dir)
    if metadata:
        return metadata.get("eval_id")
    return None


def build_run(root: Path, run_dir: Path) -> dict | None:
    prompt = extract_prompt(run_dir)
    eval_id = extract_eval_id(run_dir)
    run_id = str(run_dir.relative_to(root)).replace("/", "-").replace("\\", "-")

    return {
        "id": run_id,
        "prompt": prompt,
        "eval_id": eval_id,
        "outputs": collect_outputs(run_dir),
        "grading": load_grading(run_dir),
    }


def collect_outputs(run_dir: Path) -> list[dict]:
    outputs_dir = run_dir / "outputs"
    if not outputs_dir.is_dir():
        return []
    files = []
    for f in sorted(outputs_dir.rglob("*")):
        if f.is_file() and not any(p.name in SKIP_DIRS for p in f.relative_to(outputs_dir).parents):
            files.append(f)
    return [embed_file(f) for f in files]


def load_grading(run_dir: Path) -> dict | None:
    for parent in [run_dir, *run_dir.parents]:
        candidate = parent / "grading.json"
        text = read_text(candidate)
        if text is None:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return None


def embed_file(path: Path) -> dict:
    ext = path.suffix.lower()
    mime = get_mime_type(path)

    if ext in TEXT_EXTENSIONS:
        content = read_text(path)
        return {"name": path.name, "type": "text", "content": content or "(Error reading file)"}

    if ext in IMAGE_EXTENSIONS:
        raw = read_bytes(path)
        if raw is None:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        b64 = base64.b64encode(raw).decode("ascii")
        return {"name": path.name, "type": "image", "mime": mime, "data_uri": f"data:{mime};base64,{b64}"}

    if ext == ".pdf":
        raw = read_bytes(path)
        if raw is None:
            return {"name": path.name, "type": "error", "content": "(Error reading file)"}
        b64 = base64.b64encode(raw).decode("ascii")
        return {"name": path.name, "type": "pdf", "data_uri": f"data:{mime};base64,{b64}"}

    raw = read_bytes(path)
    if raw is None:
        return {"name": path.name, "type": "error", "content": "(Error reading file)"}
    b64 = base64.b64encode(raw).decode("ascii")
    return {"name": path.name, "type": "binary", "mime": mime, "data_uri": f"data:{mime};base64,{b64}"}


def load_feedback_map(workspace: Path) -> dict[str, str]:
    feedback_path = workspace / "feedback.json"
    text = read_text(feedback_path)
    if text is None:
        return {}
    try:
        data = json.loads(text)
        return {
            r["run_id"]: r["feedback"]
            for r in data.get("reviews", [])
            if r.get("feedback", "").strip()
        }
    except (json.JSONDecodeError, KeyError):
        return {}


def load_previous_iteration(workspace: Path) -> dict[str, dict]:
    feedback = load_feedback_map(workspace)
    previous: dict[str, dict] = {}
    for run in discover_runs(workspace):
        previous[run["id"]] = {
            "feedback": feedback.get(run["id"], ""),
            "outputs": run.get("outputs", []),
        }
    for run_id, fb in feedback.items():
        previous.setdefault(run_id, {"feedback": fb, "outputs": []})
    return previous


def build_embedded_data(
    runs: list[dict],
    skill_name: str,
    previous: dict[str, dict] | None = None,
    benchmark: dict | None = None,
) -> dict:
    previous_feedback: dict[str, str] = {}
    previous_outputs: dict[str, list[dict]] = {}
    if previous:
        for run_id, data in previous.items():
            if data.get("feedback"):
                previous_feedback[run_id] = data["feedback"]
            if data.get("outputs"):
                previous_outputs[run_id] = data["outputs"]

    embedded: dict = {
        "skill_name": skill_name,
        "runs": runs,
        "previous_feedback": previous_feedback,
        "previous_outputs": previous_outputs,
    }
    if benchmark:
        embedded["benchmark"] = benchmark
    return embedded


def generate_html(
    runs: list[dict],
    skill_name: str,
    previous: dict[str, dict] | None = None,
    benchmark: dict | None = None,
) -> str:
    viewer_path = Path(__file__).parent / "viewer.html"
    if not viewer_path.exists():
        return "<html><body><h1>Error: viewer.html not found</h1></body></html>"

    template = viewer_path.read_text()
    embedded = build_embedded_data(runs, skill_name, previous, benchmark)
    data_json = json.dumps(embedded)
    return template.replace(VIEWER_PLACEHOLDER, f"const EMBEDDED_DATA = {data_json};")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate eval review HTML")
    parser.add_argument("workspace", type=Path, help="Path to workspace iteration directory")
    parser.add_argument("--skill-name", "-n", type=str, default=None, help="Skill name for header")
    parser.add_argument(
        "--previous-workspace", type=Path, default=None,
        help="Path to previous iteration's workspace (shows old outputs and feedback)",
    )
    parser.add_argument(
        "--benchmark", type=Path, default=None,
        help="Path to benchmark.json to embed in the report",
    )
    parser.add_argument(
        "--static", "-s", type=Path, default=None,
        help="Write standalone HTML to this path instead of serving",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        logging.error(f"Error: {workspace} is not a directory")
        sys.exit(1)

    runs = discover_runs(workspace)
    if not runs:
        logging.error(f"No runs found in {workspace}")
        sys.exit(1)

    skill_name = args.skill_name or workspace.parent.name.replace("-workspace", "")

    previous: dict[str, dict] = {}
    if args.previous_workspace:
        previous = load_previous_iteration(args.previous_workspace.resolve())

    benchmark_path = args.benchmark or workspace / "benchmark.json"
    benchmark = None
    if benchmark_path.exists():
        text = read_text(benchmark_path)
        if text is not None:
            try:
                benchmark = json.loads(text)
            except json.JSONDecodeError:
                pass

    html = generate_html(runs, skill_name, previous, benchmark)

    if args.static:
        args.static.parent.mkdir(parents=True, exist_ok=True)
        args.static.write_text(html)
        logging.info(f"\n  Report written to: {args.static}\n")
    else:
        output_path = workspace / "review.html"
        output_path.write_text(html)
        logging.info(f"\n  Report written to: {output_path}\n")


if __name__ == "__main__":
    main()
