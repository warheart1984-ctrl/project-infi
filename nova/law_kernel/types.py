"""Bridge-oriented law kernel types — SQLite ledger interchange."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nova.law_kernel.models import LawRecord, LawStatus

LawId = str


@dataclass(frozen=True, slots=True)
class LawEvent:
    entry_type: str
    law_id: str
    law_hash: str
    epoch: int
    payload: dict[str, Any]
    signed_by: str
    entry_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_type": self.entry_type,
            "law_id": self.law_id,
            "law_hash": self.law_hash,
            "epoch": self.epoch,
            "payload": dict(self.payload),
            "signed_by": self.signed_by,
            "entry_id": self.entry_id,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> LawEvent:
        return cls(
            entry_type=str(row["entry_type"]),
            law_id=str(row["law_id"]),
            law_hash=str(row["law_hash"]),
            epoch=int(row["epoch"]),
            payload=dict(row.get("payload") or {}),
            signed_by=str(row.get("signed_by") or "operator"),
            entry_id=str(row["entry_id"]) if row.get("entry_id") else None,
        )


_STATUS_MAP: dict[str, LawStatus] = {
    "admitted": LawStatus.ADMITTED,
    "experimental": LawStatus.EXPERIMENTAL,
    "proposed": LawStatus.EXPERIMENTAL,
    "quarantined": LawStatus.EXPERIMENTAL,
    "deprecated": LawStatus.REVOKED,
    "revoked": LawStatus.REVOKED,
}


def _fitness_value(row: dict[str, Any]) -> float:
    if row.get("current_fitness") is not None:
        return float(row["current_fitness"])
    fitness = row.get("fitness")
    if isinstance(fitness, dict):
        return float(fitness.get("current") or 0.0)
    if fitness is not None:
        return float(fitness)
    return 0.0


def law_record_from_src(row: dict[str, Any]) -> LawRecord:
    status_raw = str(row.get("status") or "experimental").lower()
    status = _STATUS_MAP.get(status_raw, LawStatus.EXPERIMENTAL)
    epoch_raw = row.get("created_at_epoch") or row.get("epoch") or "0"
    if isinstance(epoch_raw, int):
        epoch = f"EPOCH:{epoch_raw}:T0"
    else:
        epoch = str(epoch_raw)
    return LawRecord(
        id=str(row.get("law_id") or row.get("id") or ""),
        code=str(row.get("law_id") or row.get("code") or ""),
        text=str(row.get("spec_ref") or row.get("text") or ""),
        status=status,
        fitness=_fitness_value(row),
        created_at=str(row.get("created_at") or row.get("timestamp") or "runtime"),
        epoch=epoch,
        proof_ref=str(row.get("law_hash") or row.get("proof_ref") or ""),
        domains=tuple(row.get("domains") or ()),
    )
