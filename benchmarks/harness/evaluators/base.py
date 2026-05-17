from __future__ import annotations

from abc import ABC, abstractmethod

from harness.models import Task, TrialResult


class Evaluator(ABC):
    name: str

    @abstractmethod
    def evaluate(self, result: TrialResult, task: Task) -> TrialResult:
        """Score the result in-place and return it with metrics populated."""
        ...
