"""CognitiveRuntime ABC — RAP v0.1 interface."""

# Mythic: Cognitive Runtime Family base
# Engineering: CognitiveRuntime
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.ucr.types import (
    CognitiveModeContract,
    CognitiveSituation,
    RuntimeConfig,
    RuntimeOutput,
    RuntimeTrace,
)


class CognitiveRuntime(ABC):
    """Abstract cognitive runtime conforming to Runtime Activation Protocol v0.1."""

    runtime_id: str = "cognitive.runtime.base"

    @abstractmethod
    def describe_capabilities(self) -> dict[str, Any]:
        """Return capability profile for activation matching."""

    @abstractmethod
    def accepts(self, contract: CognitiveModeContract) -> bool:
        """Whether this runtime should participate for the given contract."""

    @abstractmethod
    def configure(self, config: RuntimeConfig) -> None:
        """Apply per-turn configuration."""

    @abstractmethod
    def execute(self, situation: CognitiveSituation) -> RuntimeOutput:
        """Produce bounded runtime output for the situation."""

    @abstractmethod
    def explain(self, output: RuntimeOutput) -> RuntimeTrace:
        """Explain a prior execution output."""
