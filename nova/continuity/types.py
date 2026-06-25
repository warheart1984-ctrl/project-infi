"""Continuity bridge types — epochs, RIL export, reference binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EpochSummary:
    epoch_id: str
    epoch_number: int
    law_count: int = 0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "epoch_number": self.epoch_number,
            "law_count": self.law_count,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> EpochSummary:
        return cls(
            epoch_id=str(row.get("epoch_id") or row.get("id") or ""),
            epoch_number=int(row.get("epoch_number") or row.get("epoch") or 0),
            law_count=int(row.get("law_count") or 0),
            metadata=dict(row.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class RILExport:
    epoch_id: str
    bundle: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"epoch_id": self.epoch_id, "bundle": dict(self.bundle)}

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> RILExport:
        return cls(
            epoch_id=str(row.get("epoch_id") or ""),
            bundle=dict(row.get("bundle") or row),
        )


@dataclass(frozen=True, slots=True)
class ReferenceBinding:
    ref_hash: str
    metrics: dict[str, Any]
    bound: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_hash": self.ref_hash,
            "metrics": dict(self.metrics),
            "bound": self.bound,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> ReferenceBinding:
        return cls(
            ref_hash=str(row.get("ref_hash") or row.get("t5_ref_signal_hash") or ""),
            metrics=dict(row.get("metrics") or row),
            bound=bool(row.get("bound", True)),
        )
