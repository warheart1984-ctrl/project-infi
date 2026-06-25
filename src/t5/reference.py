"""T5 canonical reference signal — binds lineage events to identity state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ReferenceSignal:
    """Canonical T5 reference signal derived from CRK-T5 reference integrity metrics."""

    id: str
    hash: str
    issued_at: str
    issuer: str
    payload: dict[str, Any]

    @classmethod
    def current(cls, *, issuer: str = "CRK-T5-RIL") -> ReferenceSignal:
        from src.kernel.reference_service import get_reference_evaluator

        metrics = get_reference_evaluator().compute_metrics()
        payload = dict(metrics)
        digest = _canonical_hash(payload)
        return cls(
            id=f"REF-{digest[:16]}",
            hash=digest,
            issued_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            issuer=issuer,
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hash": self.hash,
            "issued_at": self.issued_at,
            "issuer": self.issuer,
            "payload": dict(self.payload),
        }
