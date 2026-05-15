# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

MAX_DESCRIPTION_LENGTH = 1024
DEFAULT_TIMEOUT = 60
RESPONSE_TRUNCATION_LENGTH = 500
DEFAULT_EXTRACT = r"<new_description>(.*?)</new_description>"


def prompt_header(current_description: str) -> str:
    return (
        "You are optimizing a skill description for an AI coding agent.\n"
        "\n"
        "The description is what the agent uses to decide whether to load and use the skill.\n"
        "It needs to trigger on the right tasks and NOT trigger on nearby but unrelated tasks.\n"
        "\n"
        "## Current description\n"
        "\n"
        f"{current_description}\n"
    )


def failure_section(queries: list[dict], title: str, intro: str) -> str:
    lines = [f"## {title}", "", intro, ""]
    for q in queries:
        lines.append(f"- {q.get('query', '')}")
    lines.append("")
    return "\n".join(lines)


def all_queries_section(queries: list[dict]) -> str:
    lines = ["## All test queries for reference", ""]
    for q in queries:
        label = "TRIGGER" if q.get("should_trigger") else "NO-TRIGGER"
        lines.append(f"- [{label}] {q.get('query', '')}")
    lines.append("")
    return "\n".join(lines)


def history_section(history: list[str]) -> str:
    lines = ["## Previously attempted descriptions (do not repeat these)", ""]
    for i, desc in enumerate(history, 1):
        lines.append(f"{i}. {desc}")
    lines.append("")
    return "\n".join(lines)


def instruction_section() -> str:
    return (
        "## Instructions\n"
        "\n"
        "Write a new description that:\n"
        "- Starts with activation-oriented phrasing like 'Use this skill when...'\n"
        "- Says what the skill does and when to use it\n"
        "- Includes concrete task verbs and artifacts from the should-trigger queries\n"
        "- Is specific enough to avoid the false positive queries\n"
        "- Stays under 1024 characters\n"
        "- Does NOT repeat previous attempts (listed above if any)\n"
        "\n"
        "Return ONLY the new description wrapped in <new_description> tags:\n"
        "\n"
        "<new_description>\n"
        "Use this skill when...\n"
        "</new_description>"
    )


def build_improvement_prompt(
    current_description: str,
    failed_queries: list[dict],
    all_queries: list[dict],
    history: list[str] | None = None,
) -> str:
    sections = [prompt_header(current_description)]
    misses = [q for q in failed_queries if q.get("should_trigger")]
    false_positives = [q for q in failed_queries if not q.get("should_trigger")]
    if misses:
        sections.append(failure_section(misses, "Should have triggered but did NOT (false negatives)", "The skill should have activated for these queries but didn't:"))
    if false_positives:
        sections.append(failure_section(false_positives, "Should NOT have triggered but did (false positives)", "The skill activated for these queries but shouldn't have:"))
    sections.append(all_queries_section(all_queries))
    if history:
        sections.append(history_section(history))
    sections.append(instruction_section())
    return "\n".join(sections)


def extract_description(output: str, extract_pattern: str) -> str | None:
    match = re.search(extract_pattern, output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def call_llm(prompt: str, command_template: str, timeout: int) -> tuple[str | None, str | None]:
    cmd_str = command_template.replace("{prompt}", prompt)
    cmd = shlex.split(cmd_str)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        combined = proc.stdout + "\n" + proc.stderr
        if proc.returncode != 0:
            return combined, f"exit code {proc.returncode}"
        return combined, None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except FileNotFoundError as e:
        return None, f"command not found: {e}"
    except Exception as e:
        return None, str(e)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Improve a skill description based on trigger eval failures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n\n"
            "  uv run scripts/improve_description.py \\\n"
            "    --description 'Use this skill when...' \\\n"
            "    --failures trigger-results.json \\\n"
            "    --command 'claude -p \"{prompt}\"' \\\n"
            "    --extract '<new_description>([\\s\\S]*?)</new_description>'\n\n"
            "  uv run scripts/improve_description.py \\\n"
            "    --description 'Use this skill when...' \\\n"
            "    --failures trigger-results.json \\\n"
            "    --command 'opencode --prompt \"{prompt}\"'"
        ),
    )
    parser.add_argument("--description", "-d", required=True, help="Current description text")
    parser.add_argument("--failures", "-f", required=True, type=Path, help="Results JSON from run_eval.py")
    parser.add_argument("--command", "-c", required=True, help="Command template with {prompt} placeholder")
    parser.add_argument("--extract", "-e", default=DEFAULT_EXTRACT,
                        help="Regex to extract description from response")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    parser.add_argument("--history", "-H", type=Path, default=None, help="Path to previous attempts JSON (list of strings)")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output path for improved description")
    return parser.parse_args()


def load_results(path: Path) -> dict:
    return json.loads(path.read_text())


def load_history(path: Path | None) -> list[str] | None:
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else None
    except (json.JSONDecodeError, OSError):
        return None


def truncate_long_description(description: str) -> str:
    if len(description) > MAX_DESCRIPTION_LENGTH:
        print(f"Warning: description is {len(description)} chars (max {MAX_DESCRIPTION_LENGTH}). Truncating.", file=sys.stderr)
        return description[:MAX_DESCRIPTION_LENGTH]
    return description


def build_output(previous_desc: str, new_desc: str, failed_queries: list[dict]) -> dict:
    return {
        "previous_description": previous_desc,
        "new_description": new_desc,
        "failed_queries_used": [
            {"id": q.get("id"), "trigger_rate": q.get("trigger_rate")}
            for q in failed_queries
        ],
    }


def write_output(output: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(output, indent=2))


def main() -> int:
    args = parse_args()
    if not args.failures.exists():
        print(f"Results file not found: {args.failures}", file=sys.stderr)
        return 1
    if "{prompt}" not in args.command:
        print("--command must contain {prompt} placeholder", file=sys.stderr)
        return 1
    results = load_results(args.failures)
    all_queries = results.get("results", [])
    failed_queries = [q for q in all_queries if not q.get("passed", True)]
    if not failed_queries:
        print("No failures found", file=sys.stderr)
        return 0
    history = load_history(args.history)
    prompt = build_improvement_prompt(args.description, failed_queries, all_queries, history)
    print(f"Improving description based on {len(failed_queries)} failed queries...", file=sys.stderr)
    print(f"Prompt length: {len(prompt)} chars", file=sys.stderr)
    response, error = call_llm(prompt, args.command, args.timeout)
    if error:
        print(f"LLM call failed: {error}", file=sys.stderr)
        if response:
            print(f"Partial output: {response[:RESPONSE_TRUNCATION_LENGTH]}", file=sys.stderr)
        return 1
    new_description = extract_description(response, args.extract)
    if not new_description:
        print("Could not extract description from response.", file=sys.stderr)
        print(f"Response (first 1000 chars): {response[:1000]}", file=sys.stderr)
        return 1
    new_description = truncate_long_description(new_description)
    output = build_output(args.description, new_description, failed_queries)
    output_path = args.output or Path("improved-description.json")
    write_output(output, output_path)
    print(f"\nImproved description written to: {output_path}", file=sys.stderr)
    print(f"\nPrevious:", file=sys.stderr)
    print(f"  {args.description}", file=sys.stderr)
    print(f"\nImproved:", file=sys.stderr)
    print(f"  {new_description}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
