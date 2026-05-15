# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(message)s")


def read_evals(path: Path) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data.get("evals", [])


def parse_frontmatter(content: str) -> dict | None:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_content = parts[1].strip()
            try:
                return yaml.safe_load(fm_content)
            except yaml.YAMLError:
                return None
    try:
        result = yaml.safe_load(content)
        if isinstance(result, dict):
            return result
        return None
    except yaml.YAMLError:
        return None


def check_file_exists(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    passed = target.exists()
    return {
        "passed": passed,
        "evidence": f"File {'exists' if passed else 'not found'}: {target}",
    }


def check_yaml_field(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    fm = parse_frontmatter(target.read_text())
    if fm is None:
        return {"passed": False, "evidence": f"YAML parse error or non-dict: {target}"}
    field = params["field"]
    value = fm.get(field)
    if value is None:
        return {"passed": False, "evidence": f"Field '{field}' not found in frontmatter"}
    if "matches" in params:
        pattern = re.compile(params["matches"])
        str_value = str(value)
        if not pattern.search(str_value):
            return {"passed": False, "evidence": f"Field '{field}' value '{str_value}' does not match pattern '{params['matches']}'"}
        return {"passed": True, "evidence": f"Field '{field}' value '{str_value}' matches pattern '{params['matches']}'"}
    if "min_length" in params:
        str_value = str(value)
        if len(str_value) < params["min_length"]:
            return {"passed": False, "evidence": f"Field '{field}' length {len(str_value)} is below minimum {params['min_length']}"}
        return {"passed": True, "evidence": f"Field '{field}' length {len(str_value)} meets minimum {params['min_length']}"}
    return {"passed": True, "evidence": f"Field '{field}' exists in frontmatter"}


def check_yaml_valid(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    content = target.read_text()
    fm = parse_frontmatter(content)
    if fm is None:
        return {"passed": False, "evidence": f"YAML parse error or non-dict: {target}"}
    return {"passed": True, "evidence": f"YAML frontmatter parsed successfully in {target.name}"}


def check_char_count(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    fm = parse_frontmatter(target.read_text())
    if fm is None:
        return {"passed": False, "evidence": f"YAML parse error or non-dict: {target}"}
    field = params["field"]
    value = fm.get(field)
    if value is None:
        return {"passed": False, "evidence": f"Field '{field}' not found in frontmatter"}
    str_value = str(value)
    char_count = len(str_value)
    max_val = params["max"]
    passed = char_count <= max_val
    return {
        "passed": passed,
        "evidence": f"Field '{field}' has {char_count} chars (max {max_val}): {'PASS' if passed else 'FAIL'}",
    }


def check_not_contains(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": True, "evidence": f"File not found (absence confirmed): {target}"}
    content = target.read_text()
    text = params["text"]
    passed = text not in content
    return {
        "passed": passed,
        "evidence": f"Text '{text}' {'not found' if passed else 'found'} in {target.name}",
    }


def check_contains(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    content = target.read_text()
    text = params["text"]
    passed = text in content
    return {
        "passed": passed,
        "evidence": f"Text '{text}' {'found' if passed else 'not found'} in {target.name}",
    }


def check_contains_regex(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    content = target.read_text()
    pattern = re.compile(params["pattern"])
    passed = bool(pattern.search(content))
    return {
        "passed": passed,
        "evidence": f"Pattern '{params['pattern']}' {'matched' if passed else 'not matched'} in {target.name}",
    }


def check_not_empty(outputs_dir: Path, params: dict) -> dict:
    target = outputs_dir / params["path"]
    if not target.exists():
        return {"passed": False, "evidence": f"File not found: {target}"}
    content = target.read_text()
    passed = bool(content.strip())
    return {
        "passed": passed,
        "evidence": f"File {target.name} is {'non-empty' if passed else 'empty or whitespace-only'}",
    }


CHECKERS = {
    "file_exists": check_file_exists,
    "yaml_field": check_yaml_field,
    "yaml_valid": check_yaml_valid,
    "char_count": check_char_count,
    "not_contains": check_not_contains,
    "contains": check_contains,
    "contains_regex": check_contains_regex,
    "not_empty": check_not_empty,
}


def run_checks(evals: list[dict], outputs_dir: Path) -> list[dict]:
    expectations = []
    for eval_case in evals:
        assertions = eval_case.get("assertions", [])
        for assertion in assertions:
            if isinstance(assertion, str):
                continue
            checks = assertion.get("checks")
            if not checks:
                continue
            results = []
            all_passed = True
            for check in checks:
                check_type = check["type"]
                checker = CHECKERS.get(check_type)
                if checker is None:
                    results.append({"passed": False, "evidence": f"Unknown check type: {check_type}"})
                    all_passed = False
                    continue
                result = checker(outputs_dir, check)
                results.append(result)
                if not result["passed"]:
                    all_passed = False
            expectations.append({
                "text": assertion["text"],
                "passed": all_passed,
                "evidence": "; ".join(r["evidence"] for r in results),
            })
    return expectations


def count_output_chars(outputs_dir: Path) -> int:
    total = 0
    for f in outputs_dir.rglob("*"):
        if f.is_file():
            try:
                total += len(f.read_bytes())
            except OSError:
                pass
    return total


def produce_checks_json(expectations: list[dict], outputs_dir: Path) -> dict:
    total = len(expectations)
    passed = sum(1 for e in expectations if e["passed"])
    failed = total - passed
    return {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
        },
        "output_chars": count_output_chars(outputs_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic checks on eval output files")
    parser.add_argument("--evals-json", type=Path, required=True, help="Path to evals.json")
    parser.add_argument("--outputs-dir", type=Path, required=True, help="Path to run outputs directory")
    parser.add_argument("--run-dir", type=Path, required=True, help="Path to run directory for writing checks.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.evals_json.exists():
        logging.error(f"evals.json not found: {args.evals_json}")
        return 1
    if not args.outputs_dir.exists():
        logging.error(f"outputs dir not found: {args.outputs_dir}")
        return 1
    args.run_dir.mkdir(parents=True, exist_ok=True)
    evals = read_evals(args.evals_json)
    expectations = run_checks(evals, args.outputs_dir)
    checks = produce_checks_json(expectations, args.outputs_dir)
    output_path = args.run_dir / "checks.json"
    output_path.write_text(json.dumps(checks, indent=2))
    logging.info(f"Wrote {len(expectations)} check results to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
