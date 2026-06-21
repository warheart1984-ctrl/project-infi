"""Lineage model for convergence algebra, continuity lattice, and LCI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Lineage:
    """Semantic lineage L with continuity trace K(L) and generativity G(L)."""

    lineage_id: str
    event_ids: frozenset[str]
    meaning_class: str
    generativity: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "event_ids": sorted(self.event_ids),
            "meaning_class": self.meaning_class,
            "generativity": self.generativity,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> Lineage:
        return cls(
            lineage_id=str(row["lineage_id"]),
            event_ids=frozenset(str(item) for item in row.get("event_ids") or []),
            meaning_class=str(row.get("meaning_class") or "unknown"),
            generativity=float(row.get("generativity") or 0.0),
            metadata=dict(row.get("metadata") or {}),
        )


def continuity_trace(lineage: Lineage) -> frozenset[str]:
    """K(L) — continuity trace as event set."""

    return lineage.event_ids


def generativity(lineage: Lineage) -> float:
    """G(L) — extent of created structure."""

    return float(lineage.generativity)
