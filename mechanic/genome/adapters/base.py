"""Base adapter protocol for Process Genome extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class GenomeAdapter(ABC):
    adapter_id: str

    @abstractmethod
    def describe(self, repo_path: Path) -> dict[str, Any]:
        """Return adapter metadata for observe mode."""

    @abstractmethod
    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        """Mutate genome in place; return adapter summary."""


def run_adapters(
    repo_path: Path,
    genome: dict[str, Any],
    *,
    adapter_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    from mechanic.genome.adapters.registry import get_adapter, list_adapter_ids

    ids = adapter_ids or list_adapter_ids()
    summaries: list[dict[str, Any]] = []
    for adapter_id in ids:
        adapter = get_adapter(adapter_id)
        summary = adapter.extract(repo_path, genome)
        summary["adapter_id"] = adapter_id
        summaries.append(summary)
    genome["adapters"] = summaries
    return summaries


def list_adapters() -> list[str]:
    from mechanic.genome.adapters.registry import list_adapter_ids

    return list_adapter_ids()
