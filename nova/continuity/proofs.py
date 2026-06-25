from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class ContinuityProof:
    epoch_id: str
    identity_hash: str
    reference_integrity_hash: str
    boundary_stability_hash: str
    pit_evolution_hash: str
    reflexive_health_hash: str
    perception_health_hash: str
    amendment_history_hash: str
    proof_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "identity_hash": self.identity_hash,
            "reference_integrity_hash": self.reference_integrity_hash,
            "boundary_stability_hash": self.boundary_stability_hash,
            "pit_evolution_hash": self.pit_evolution_hash,
            "reflexive_health_hash": self.reflexive_health_hash,
            "perception_health_hash": self.perception_health_hash,
            "amendment_history_hash": self.amendment_history_hash,
            "proof_id": self.proof_id,
        }


def _section_hash(section: Any) -> str:
    blob = json.dumps(section, sort_keys=True, separators=(",", ":"))
    return sha256(blob.encode("utf-8")).hexdigest()


def proof_from_cockpit_summary(epoch_id: str, summary: dict[str, Any]) -> ContinuityProof:
    identity_hash = _section_hash(summary.get("identity_history", {}))
    reference_integrity_hash = _section_hash(summary.get("reference_integrity", {}))
    boundary_stability_hash = _section_hash(summary.get("boundary_detection", {}))
    pit_evolution_hash = _section_hash(summary.get("pit_evolution", {}))
    reflexive_health_hash = _section_hash(summary.get("reflexive_evaluation", {}))
    perception_health_hash = _section_hash(summary.get("perception_health", {}))
    amendment_history_hash = _section_hash(summary.get("amendment_history", {}))
    proof_seed = "|".join(
        [
            epoch_id,
            identity_hash,
            reference_integrity_hash,
            boundary_stability_hash,
            pit_evolution_hash,
            reflexive_health_hash,
            perception_health_hash,
            amendment_history_hash,
        ]
    )
    proof_id = sha256(proof_seed.encode("utf-8")).hexdigest()[:16]
    return ContinuityProof(
        epoch_id=epoch_id,
        identity_hash=identity_hash,
        reference_integrity_hash=reference_integrity_hash,
        boundary_stability_hash=boundary_stability_hash,
        pit_evolution_hash=pit_evolution_hash,
        reflexive_health_hash=reflexive_health_hash,
        perception_health_hash=perception_health_hash,
        amendment_history_hash=amendment_history_hash,
        proof_id=proof_id,
    )
