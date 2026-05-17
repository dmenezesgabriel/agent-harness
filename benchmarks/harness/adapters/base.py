from __future__ import annotations

from abc import ABC, abstractmethod

from harness.models import Condition, Task, TrialResult


class AgentAdapter(ABC):
    name: str

    @abstractmethod
    def run(self, task: Task, condition: Condition, trial_index: int) -> TrialResult:
        """Run one trial of a task under the given condition and return a TrialResult."""
        ...
