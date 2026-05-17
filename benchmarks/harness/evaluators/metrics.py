"""Core metric computations: precision, recall, F1, Cohen's kappa, effect size."""
from __future__ import annotations

import math


def precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def cohens_kappa(observed_agreement: float, expected_agreement: float) -> float:
    if expected_agreement >= 1.0:
        return 1.0
    return (observed_agreement - expected_agreement) / (1 - expected_agreement)


def cohens_d(mean_a: float, mean_b: float, std_a: float, std_b: float) -> float:
    pooled_std = math.sqrt((std_a**2 + std_b**2) / 2)
    return (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    n = len(values)
    m = sum(values) / n
    variance = sum((x - m) ** 2 for x in values) / n
    return m, math.sqrt(variance)


def section_present(text: str, section_name: str) -> bool:
    """Check whether a markdown section heading is present and has non-empty content."""
    lines = text.splitlines()
    in_section = False
    has_content = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and section_name.lower() in stripped.lower():
            in_section = True
            continue
        if in_section:
            if stripped.startswith("#"):
                break
            if stripped:
                has_content = True
    return in_section and has_content
