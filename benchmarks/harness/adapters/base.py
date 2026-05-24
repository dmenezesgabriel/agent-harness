from __future__ import annotations

from abc import ABC, abstractmethod

from harness.models import Task, TaskResult


class AgentAdapter(ABC):
    name: str

    @abstractmethod
    def run(self, task: Task) -> TaskResult:
        """Run a task and return a TaskResult."""
        ...
