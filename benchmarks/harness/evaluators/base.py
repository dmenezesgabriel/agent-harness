from __future__ import annotations

from abc import ABC, abstractmethod

from harness.models import Task, TaskResult


class Evaluator(ABC):
    name: str

    @abstractmethod
    def evaluate(self, result: TaskResult, task: Task) -> TaskResult:
        """Score the result in-place and return it with metrics populated."""
        ...
