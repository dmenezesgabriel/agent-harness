#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["sentence-transformers>=3.0,<4", "scikit-learn>=1.5,<2"]
# ///
"""Create embedding-aware train/validation splits for eval manifests.

Usage:
  uv run scripts/skill-evals/semantic_split.py --input skills/software-feature-planning/evals/evals.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def load_payload(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def get_cases(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("evals"), list):
        return payload["evals"]
    raise ValueError("Input JSON must be a list or an object with an 'evals' array")


def set_cases(payload: Any, cases: list[dict[str, Any]]) -> Any:
    if isinstance(payload, list):
        return cases
    updated = dict(payload)
    updated["evals"] = cases
    return updated


def bucket_key(case: dict[str, Any]) -> tuple[str, str]:
    kind = str(case.get("kind", "generic"))
    if kind == "trigger":
        return kind, str(bool(case.get("should_trigger", False)))
    return kind, "all"


def select_diverse_indexes(similarity_matrix: list[list[float]], count: int, seed: int) -> list[int]:
    total = len(similarity_matrix)
    if count <= 0:
        return []
    if count >= total:
        return list(range(total))

    rng = random.Random(seed)
    selected = [rng.randrange(total)]
    remaining = set(range(total)) - set(selected)
    while len(selected) < count and remaining:
        candidate = min(
            remaining,
            key=lambda index: max(float(similarity_matrix[index][chosen]) for chosen in selected),
        )
        selected.append(candidate)
        remaining.remove(candidate)
    return sorted(selected)


def compute_leakage(split_cases: list[dict[str, Any]], embeddings: list[list[float]], threshold: float) -> dict[str, Any]:
    if len(split_cases) < 2:
        return {"cross_split_leakage_count": 0, "cross_split_pairs": [], "mean_nearest_similarity": 0.0}

    similarity = cosine_similarity(embeddings)
    leak_pairs: list[dict[str, Any]] = []
    nearest_values: list[float] = []
    for index, case in enumerate(split_cases):
        nearest_index = max((candidate for candidate in range(len(split_cases)) if candidate != index), key=lambda candidate: float(similarity[index][candidate]))
        nearest_score = float(similarity[index][nearest_index])
        nearest_values.append(nearest_score)
        if nearest_score >= threshold and case.get("split") != split_cases[nearest_index].get("split"):
            leak_pairs.append(
                {
                    "id": str(case.get("id")),
                    "nearest_id": str(split_cases[nearest_index].get("id")),
                    "similarity": round(nearest_score, 4),
                    "split": case.get("split"),
                    "nearest_split": split_cases[nearest_index].get("split"),
                }
            )
    return {
        "cross_split_leakage_count": len(leak_pairs),
        "cross_split_pairs": leak_pairs,
        "mean_nearest_similarity": (sum(nearest_values) / len(nearest_values)) if nearest_values else 0.0,
    }


def semantic_split(cases: list[dict[str, Any]], validation_ratio: float, seed: int, model_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model = SentenceTransformer(model_name)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        buckets[bucket_key(case)].append(dict(case))

    split_cases: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {"buckets": {}}
    for offset, (key, bucket) in enumerate(sorted(buckets.items(), key=lambda item: item[0])):
        if not bucket:
            continue
        validation_count = int(round(len(bucket) * validation_ratio))
        validation_count = max(0, min(validation_count, len(bucket)))
        prompts = [str(case.get("prompt", "")) for case in bucket]
        embeddings = model.encode(prompts, normalize_embeddings=True)
        similarity = cosine_similarity(embeddings).tolist()
        selected_indexes = set(select_diverse_indexes(similarity, validation_count, seed + offset))

        for index, case in enumerate(bucket):
            case["split"] = "validation" if index in selected_indexes else "train"
            split_cases.append(case)

        diagnostics["buckets"][f"{key[0]}:{key[1]}"] = {
            "total": len(bucket),
            "validation": len(selected_indexes),
            "train": len(bucket) - len(selected_indexes),
        }

    combined_prompts = [str(case.get("prompt", "")) for case in split_cases]
    combined_embeddings = model.encode(combined_prompts, normalize_embeddings=True)
    diagnostics["similarity"] = compute_leakage(split_cases, combined_embeddings.tolist(), threshold=0.85)
    return split_cases, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Input JSON file")
    parser.add_argument("--output", type=Path, help="Write the split JSON here")
    parser.add_argument("--report", type=Path, help="Write semantic split diagnostics here")
    parser.add_argument("--validation-ratio", type=float, default=0.4, help="Fraction of each semantic bucket sent to validation")
    parser.add_argument("--seed", type=int, default=7, help="Selection seed")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="SentenceTransformer model name")
    args = parser.parse_args()

    payload = load_payload(args.input)
    cases = get_cases(payload)
    split, diagnostics = semantic_split(cases, args.validation_ratio, args.seed, args.model)
    result = set_cases(payload, split)

    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    report_text = json.dumps(diagnostics, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(report_text + "\n", encoding="utf-8")
    print(report_text, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
