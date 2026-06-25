from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nova.law_kernel.models import Intent


@dataclass
class CognitiveLobe:
    name: str
    process: Callable[[Intent], Intent]


class CortexRegistry:
    def __init__(self) -> None:
        self._lobes: dict[str, CognitiveLobe] = {}

    def register(self, lobe: CognitiveLobe) -> None:
        self._lobes[lobe.name] = lobe

    def run_pipeline(self, intent: Intent, pipeline: list[str]) -> Intent:
        current = intent
        for name in pipeline:
            lobe = self._lobes[name]
            current = lobe.process(current)
        return current
