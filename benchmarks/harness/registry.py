"""Component registry: maps string names to component factories.

Adapters and evaluators are pre-registered in their respective __init__.py
files. Third parties can register custom components by calling
adapter_registry.register(...) before invoking the runner.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, TypeVar

if TYPE_CHECKING:
    from harness.adapters.base import AgentAdapter
    from harness.evaluators.base import Evaluator

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[str, Callable[[], T]] = {}

    def register(self, name: str, factory: Callable[[], T]) -> None:
        if name in self._entries:
            raise ValueError(
                f"'{name}' is already registered. Existing: {sorted(self._entries)}"
            )
        self._entries[name] = factory

    def resolve(self, name: str) -> T:
        if name not in self._entries:
            raise KeyError(
                f"Unknown component '{name}'. Known: {sorted(self._entries)}"
            )
        return self._entries[name]()

    def list_names(self) -> list[str]:
        return sorted(self._entries)


adapter_registry: "Registry[AgentAdapter]" = Registry()
evaluator_registry: "Registry[Evaluator]" = Registry()
