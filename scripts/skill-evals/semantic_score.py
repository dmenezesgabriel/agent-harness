#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["sentence-transformers>=3.0,<4", "scikit-learn>=1.5,<2"]
# ///
"""Run embedding-based routing diagnostics for trigger eval prompts.

Usage:
  uv run scripts/skill-evals/semantic_score.py \
    --manifest skills/software-feature-planning/evals/evals.json \
    --runs runs/triggers.json \
    --skill-dir skills/software-feature-planning \
    --skills-dir skills
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

FRONTMATTER_PREFIX = "---\n"


@dataclass(frozen=True)
class SemanticCase:
    id: str
    prompt: str
    should_trigger: bool
    triggered: bool
    target_skill: str
    target_similarity: float
    target_rank: int
    route_top1_hit: bool | None
    route_topk_hit: bool | None
    margin_vs_best_non_target: float
    top_routes: list[dict[str, Any]] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_lines(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.lstrip().startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list of run objects")
        return payload
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith(FRONTMATTER_PREFIX):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", len(FRONTMATTER_PREFIX))
    if end == -1:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    block = text[len(FRONTMATTER_PREFIX):end]
    frontmatter: dict[str, str] = {}
    for raw_line in block.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def load_skill_descriptions(skills_dir: Path) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        frontmatter = parse_frontmatter(skill_md)
        name = frontmatter.get("name", skill_md.parent.name)
        description = frontmatter.get("description", "")
        if name:
            descriptions[str(name)] = str(description)
    return descriptions


def get_trigger_cases(payload: Any) -> tuple[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        raise ValueError("Manifest must be a JSON object with skill_name and evals")
    skill_name = str(payload.get("skill_name", "")).strip()
    if not skill_name:
        raise ValueError("Manifest must include a non-empty 'skill_name'")
    cases = payload.get("evals")
    if not isinstance(cases, list):
        raise ValueError("Manifest must include an 'evals' array")
    trigger_cases = [case for case in cases if isinstance(case, dict) and (case.get("kind") == "trigger" or "should_trigger" in case)]
    return skill_name, trigger_cases


def pair_runs(cases: list[dict[str, Any]], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_map: dict[str, dict[str, Any]] = {}
    for run in runs:
        run_id = str(run.get("id"))
        if not run_id or run_id == "None":
            raise ValueError("Each run must include a non-empty 'id'")
        if run_id in run_map:
            raise ValueError(f"Duplicate run id: {run_id}")
        run_map[run_id] = run

    case_ids = {str(case.get("id")) for case in cases}
    missing = [case_id for case_id in case_ids if case_id not in run_map]
    extra = [run_id for run_id in run_map if run_id not in case_ids]
    if missing:
        raise ValueError(f"Missing runs for case ids: {missing}")
    if extra:
        raise ValueError(f"Unexpected run ids: {extra}")

    paired: list[dict[str, Any]] = []
    for case in cases:
        merged = dict(case)
        run = run_map[str(case.get("id"))]
        for key, value in run.items():
            if key != "id":
                merged[key] = value
        paired.append(merged)
    return paired


def summarize(cases: list[SemanticCase], top_k: int) -> dict[str, Any]:
    positives = [case for case in cases if case.should_trigger]
    negatives = [case for case in cases if not case.should_trigger]
    failures = [case for case in cases if case.failure_reasons]

    summary: dict[str, Any] = {
        "case_count": len(cases),
        "positive_case_count": len(positives),
        "negative_case_count": len(negatives),
        "failure_case_count": len(failures),
    }
    if positives:
        summary["positive_route_top1_accuracy"] = sum(1 for case in positives if case.route_top1_hit) / len(positives)
        summary[f"positive_route_top{top_k}_accuracy"] = sum(1 for case in positives if case.route_topk_hit) / len(positives)
        summary["positive_target_similarity_mean"] = sum(case.target_similarity for case in positives) / len(positives)
        summary["positive_margin_mean"] = sum(case.margin_vs_best_non_target for case in positives) / len(positives)
        summary["positive_target_rank_mean"] = sum(case.target_rank for case in positives) / len(positives)
    if negatives:
        summary["negative_target_similarity_mean"] = sum(case.target_similarity for case in negatives) / len(negatives)
        summary["negative_margin_mean"] = sum(case.margin_vs_best_non_target for case in negatives) / len(negatives)
        summary["negative_target_rank_mean"] = sum(case.target_rank for case in negatives) / len(negatives)
    return summary


def build_failure_clusters(cases: list[SemanticCase], embeddings: list[list[float]], max_clusters: int) -> list[dict[str, Any]]:
    failed_items = [(index, case) for index, case in enumerate(cases) if case.failure_reasons]
    if not failed_items:
        return []
    failed_indexes = [index for index, _ in failed_items]
    failed_embeddings = [embeddings[index] for index in failed_indexes]
    if len(failed_items) == 1:
        _, case = failed_items[0]
        return [{
            "cluster_id": 0,
            "size": 1,
            "representative_prompt": case.prompt,
            "failure_reason_counts": dict(Counter(case.failure_reasons)),
            "top_route_counts": {case.top_routes[0]["skill"]: 1} if case.top_routes else {},
            "members": [asdict(case)],
        }]

    cluster_count = min(max_clusters, max(1, int(round(math.sqrt(len(failed_items))))), len(failed_items))
    model = KMeans(n_clusters=cluster_count, random_state=7, n_init=10)
    labels = model.fit_predict(failed_embeddings)

    clusters: list[dict[str, Any]] = []
    for cluster_id in range(cluster_count):
        members = [(failed_indexes[position], case) for position, (_, case) in enumerate(failed_items) if int(labels[position]) == cluster_id]
        member_indexes = [index for index, _ in members]
        member_cases = [case for _, case in members]
        member_embeddings = [embeddings[index] for index in member_indexes]
        centroid = model.cluster_centers_[cluster_id]
        representative_position = max(range(len(member_embeddings)), key=lambda pos: float(cosine_similarity([member_embeddings[pos]], [centroid])[0][0]))
        representative_case = member_cases[representative_position]
        reason_counts = Counter(reason for case in member_cases for reason in case.failure_reasons)
        route_counts = Counter(case.top_routes[0]["skill"] for case in member_cases if case.top_routes)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "size": len(member_cases),
                "representative_prompt": representative_case.prompt,
                "failure_reason_counts": dict(reason_counts),
                "top_route_counts": dict(route_counts),
                "members": [asdict(case) for case in member_cases],
            }
        )
    return clusters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Skill eval manifest")
    parser.add_argument("--runs", type=Path, required=True, help="JSON or JSONL trigger runs file")
    parser.add_argument("--skill-dir", type=Path, required=True, help="Skill directory or generated variant directory")
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"), help="Root skills directory for routing candidates")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k route hit threshold for positives")
    parser.add_argument("--cluster-failures", action="store_true", help="Cluster failed prompts using embeddings")
    parser.add_argument("--max-clusters", type=int, default=5, help="Maximum number of failure clusters")
    parser.add_argument("--output", type=Path, help="Write semantic report here")
    args = parser.parse_args()

    manifest_payload = read_json(args.manifest)
    target_skill_name, cases = get_trigger_cases(manifest_payload)
    runs = read_json_lines(args.runs)
    paired = pair_runs(cases, runs)

    skill_dir = args.skill_dir.expanduser().resolve()
    target_frontmatter = parse_frontmatter(skill_dir / "SKILL.md")
    target_description = target_frontmatter.get("description", "")

    skills_dir = args.skills_dir.expanduser().resolve()
    descriptions = load_skill_descriptions(skills_dir)
    descriptions[target_skill_name] = target_description
    if not descriptions:
        raise ValueError(f"No skills found in {skills_dir}")

    model = SentenceTransformer(args.model)
    skill_names = sorted(descriptions)
    skill_texts = [descriptions[name] for name in skill_names]
    prompts = [str(case.get("prompt", "")) for case in paired]

    skill_embeddings = model.encode(skill_texts, normalize_embeddings=True)
    prompt_embeddings = model.encode(prompts, normalize_embeddings=True)
    routing_matrix = cosine_similarity(prompt_embeddings, skill_embeddings)

    top_k = max(1, args.top_k)
    semantic_cases: list[SemanticCase] = []
    for index, case in enumerate(paired):
        row = routing_matrix[index]
        ranked_indexes = sorted(range(len(skill_names)), key=lambda item: float(row[item]), reverse=True)
        ranked_routes = [
            {"skill": skill_names[skill_index], "score": round(float(row[skill_index]), 4)}
            for skill_index in ranked_indexes[: min(len(skill_names), top_k)]
        ]
        target_index = skill_names.index(target_skill_name)
        target_rank = ranked_indexes.index(target_index) + 1
        target_similarity = float(row[target_index])
        best_non_target_index = next((item for item in ranked_indexes if item != target_index), target_index)
        best_non_target_score = float(row[best_non_target_index]) if best_non_target_index != target_index else target_similarity
        margin = target_similarity - best_non_target_score

        should_trigger = bool(case.get("should_trigger", False))
        triggered = bool(case.get("triggered", False))
        route_top1_hit = (target_rank == 1) if should_trigger else None
        route_topk_hit = (target_rank <= top_k) if should_trigger else None

        failure_reasons: list[str] = []
        if triggered != should_trigger:
            failure_reasons.append("trigger_mismatch")
        if should_trigger and target_rank != 1:
            failure_reasons.append("route_miss_top1")

        semantic_cases.append(
            SemanticCase(
                id=str(case.get("id", index)),
                prompt=prompts[index],
                should_trigger=should_trigger,
                triggered=triggered,
                target_skill=target_skill_name,
                target_similarity=round(target_similarity, 4),
                target_rank=target_rank,
                route_top1_hit=route_top1_hit,
                route_topk_hit=route_topk_hit,
                margin_vs_best_non_target=round(margin, 4),
                top_routes=ranked_routes,
                failure_reasons=failure_reasons,
            )
        )

    summary = summarize(semantic_cases, top_k)
    route_confusions = Counter(
        case.top_routes[0]["skill"]
        for case in semantic_cases
        if case.should_trigger and case.route_top1_hit is False and case.top_routes
    )
    clusters = build_failure_clusters(semantic_cases, prompt_embeddings.tolist(), args.max_clusters) if args.cluster_failures else []

    report = {
        "model": args.model,
        "target_skill": target_skill_name,
        "candidate_skills": skill_names,
        "summary": summary,
        "route_confusions": dict(route_confusions),
        "cases": [asdict(case) for case in semantic_cases],
        "failure_clusters": clusters,
    }

    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
