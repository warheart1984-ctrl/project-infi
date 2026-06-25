from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class StewardId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class StewardSignature:
    steward_id: StewardId
    signed_at: str
    t5_ref_signal_hash: str
    lineage_event_id: str


@dataclass
class AmendmentProposal:
    id: str
    steward_id: StewardId
    payload: dict[str, Any]
    status: str = "proposed"
    created_at: str = field(default_factory=_now_iso)
    lineage_event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "steward_id": str(self.steward_id),
            "payload": dict(self.payload),
            "status": self.status,
            "created_at": self.created_at,
            "lineage_event_id": self.lineage_event_id,
        }


@dataclass
class RatifiedAmendment:
    proposal_id: str
    signatures: list[StewardSignature]
    payload: dict[str, Any]
    ratified_at: str = field(default_factory=_now_iso)
    lineage_event_id: str = ""
    t5_ref_signal_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "signatures": [
                {
                    "steward_id": str(sig.steward_id),
                    "signed_at": sig.signed_at,
                    "t5_ref_signal_hash": sig.t5_ref_signal_hash,
                    "lineage_event_id": sig.lineage_event_id,
                }
                for sig in self.signatures
            ],
            "payload": dict(self.payload),
            "ratified_at": self.ratified_at,
            "lineage_event_id": self.lineage_event_id,
            "t5_ref_signal_hash": self.t5_ref_signal_hash,
        }
