# /// script
# requires-python = ">=3.11"
# ///
"""Aggregate individual eval run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- config_stats with mean, stddev, min, max for each metric
- delta between primary and baseline configurations

Usage:
    uv run scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>
    uv run scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name> --output-dir <path>
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


ROUND_PRECISION = 4
EMPTY_STATS = {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}


def grading_path(run_dir):
    p = run_dir / "grading.json"
    return p if p.exists() else None


def eval_identifier(eval_dir, default):
    meta = eval_dir / "eval_metadata.json"
    if not meta.exists():
        return default
    try:
        return json.loads(meta.read_text()).get("eval_id", default)
    except (json.JSONDecodeError, OSError):
        return default


def parse_run(eval_id, run_dir, grading):
    run_number = int(run_dir.name.split("-")[1])
    summary = grading.get("summary", {})
    timing = grading.get("timing", {})
    metrics = grading.get("execution_metrics", {})

    time_seconds = timing.get("total_duration_seconds", 0.0)
    tokens = 0

    if not time_seconds:
        timing_file = run_dir / "timing.json"
        if timing_file.exists():
            try:
                tdata = json.loads(timing_file.read_text())
                time_seconds = tdata.get("total_duration_seconds", 0.0)
                tokens = tdata.get("total_tokens", 0)
            except (json.JSONDecodeError, OSError):
                pass

    if not tokens:
        tokens = metrics.get("output_chars", 0)

    return {
        "eval_id": eval_id,
        "run_number": run_number,
        "pass_rate": summary.get("pass_rate", 0.0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "total": summary.get("total", 0),
        "time_seconds": time_seconds,
        "tokens": tokens,
        "tool_calls": metrics.get("total_tool_calls", 0),
        "errors": metrics.get("errors_encountered", 0),
        "expectations": grading.get("expectations", []),
    }


def collect_runs(iteration_dir):
    runs = []
    for eval_dir in sorted(iteration_dir.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            for run_dir in sorted(config_dir.glob("run-*")):
                if not run_dir.is_dir():
                    continue
                grading = grading_path(run_dir)
                if grading is None:
                    continue
                config_name = config_dir.name
                eid = eval_identifier(eval_dir, eval_dir.name)
                try:
                    data = json.loads(grading.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                runs.append((config_name, parse_run(eid, run_dir, data)))
    return runs


def gather_config_groups(runs):
    configs = {config for config, _ in runs}
    return {config: [r for c, r in runs if c == config] for config in configs}


def stats_summary(values):
    if not values:
        return dict(EMPTY_STATS)
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    stddev = math.sqrt(variance)
    return {
        "mean": round(mean, ROUND_PRECISION),
        "stddev": round(stddev, ROUND_PRECISION),
        "min": round(min(values), ROUND_PRECISION),
        "max": round(max(values), ROUND_PRECISION),
    }


def compute_config_stats(groups):
    return {
        config: {
            metric: stats_summary([r[metric] for r in runs])
            for metric in ("pass_rate", "time_seconds", "tokens")
        }
        if runs
        else {metric: dict(EMPTY_STATS) for metric in ("pass_rate", "time_seconds", "tokens")}
        for config, runs in sorted(groups.items())
    }


def compute_delta(config_stats):
    configs = list(config_stats.keys())
    if not configs:
        return {"pass_rate": "\u2014", "time_seconds": "\u2014", "tokens": "\u2014"}
    primary = config_stats[configs[0]]
    baseline = config_stats[configs[1]] if len(configs) >= 2 else EMPTY_STATS
    return {
        "pass_rate": f"{primary['pass_rate']['mean'] - baseline['pass_rate']['mean']:+.2f}",
        "time_seconds": f"{primary['time_seconds']['mean'] - baseline['time_seconds']['mean']:+.1f}",
        "tokens": f"{primary['tokens']['mean'] - baseline['tokens']['mean']:+.0f}",
    }


def build_run_entries(groups):
    return [
        {
            "eval_id": r["eval_id"],
            "configuration": config,
            "run_number": r["run_number"],
            "result": {
                "pass_rate": r["pass_rate"],
                "passed": r["passed"],
                "failed": r["failed"],
                "total": r["total"],
                "time_seconds": r["time_seconds"],
                "tokens": r["tokens"],
                "tool_calls": r["tool_calls"],
                "errors": r["errors"],
            },
            "expectations": r["expectations"],
        }
        for config, runs in groups.items()
        for r in runs
    ]


def collect_eval_ids(run_entries):
    return sorted({r["eval_id"] for r in run_entries})


def generate_benchmark(iteration_dir, skill_name=""):
    runs = collect_runs(iteration_dir)
    groups = gather_config_groups(runs)
    config_stats = compute_config_stats(groups)
    delta = compute_delta(config_stats)
    run_entries = build_run_entries(groups)
    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": collect_eval_ids(run_entries),
        },
        "runs": run_entries,
        "config_stats": config_stats,
        "delta": delta,
    }


def markdown_table(benchmark):
    metadata = benchmark["metadata"]
    config_stats = benchmark["config_stats"]
    delta = benchmark["delta"]
    configs = list(config_stats.keys())
    config_a = configs[0].replace("_", " ").title() if configs else "Config A"
    config_b = configs[1].replace("_", " ").title() if len(configs) >= 2 else "Config B"

    a_pass = config_stats.get(configs[0], {}).get("pass_rate", EMPTY_STATS) if configs else EMPTY_STATS
    b_pass = config_stats.get(configs[1], {}).get("pass_rate", EMPTY_STATS) if len(configs) >= 2 else EMPTY_STATS
    a_time = config_stats.get(configs[0], {}).get("time_seconds", EMPTY_STATS) if configs else EMPTY_STATS
    b_time = config_stats.get(configs[1], {}).get("time_seconds", EMPTY_STATS) if len(configs) >= 2 else EMPTY_STATS
    a_tok = config_stats.get(configs[0], {}).get("tokens", EMPTY_STATS) if configs else EMPTY_STATS
    b_tok = config_stats.get(configs[1], {}).get("tokens", EMPTY_STATS) if len(configs) >= 2 else EMPTY_STATS

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata.get('evals_run', [])))}",
        "",
        "## Summary",
        "",
        f"| Metric | {config_a} | {config_b} | Delta |",
        "|--------|------------|---------------|-------|",
        f"| Pass Rate | {a_pass['mean']*100:.0f}% \u00b1 {a_pass['stddev']*100:.0f}% |"
        f" {b_pass['mean']*100:.0f}% \u00b1 {b_pass['stddev']*100:.0f}% |"
        f" {delta['pass_rate']} |",
        f"| Time | {a_time['mean']:.1f}s \u00b1 {a_time['stddev']:.1f}s |"
        f" {b_time['mean']:.1f}s \u00b1 {b_time['stddev']:.1f}s |"
        f" {delta['time_seconds']}s |",
        f"| Tokens | {a_tok['mean']:.0f} \u00b1 {a_tok['stddev']:.0f} |"
        f" {b_tok['mean']:.0f} \u00b1 {b_tok['stddev']:.0f} |"
        f" {delta['tokens']} |",
    ]

    return "\n".join(lines)


def write_outputs(benchmark, output_dir):
    json_path = output_dir / "benchmark.json"
    json_path.write_text(json.dumps(benchmark, indent=2))
    print(f"Generated: {json_path}")

    md_path = output_dir / "benchmark.md"
    md_path.write_text(markdown_table(benchmark))
    print(f"Generated: {md_path}")


def print_summary(benchmark):
    config_stats = benchmark["config_stats"]
    delta = benchmark["delta"]
    print()
    print("Summary:")
    for config in config_stats:
        pr = config_stats[config]["pass_rate"]["mean"]
        print(f"  {config.replace('_', ' ').title()}: {pr*100:.1f}% pass rate")
    print(f"  Delta: {delta['pass_rate']}")


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate eval results into benchmark")
    parser.add_argument("iteration_dir", type=Path)
    parser.add_argument("--skill-name", default="")
    parser.add_argument("--output-dir", "-o", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.iteration_dir.exists():
        print(f"Directory not found: {args.iteration_dir}", file=sys.stderr)
        return 1
    benchmark = generate_benchmark(args.iteration_dir, args.skill_name)
    output_dir = args.output_dir or args.iteration_dir
    write_outputs(benchmark, output_dir)
    print_summary(benchmark)
    return 0


if __name__ == "__main__":
    sys.exit(main())
