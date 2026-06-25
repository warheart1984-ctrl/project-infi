from __future__ import annotations

from nova.continuity.proofs import ContinuityProof, proof_from_cockpit_summary
from nova.crk.cockpit.summary_builder import build_cockpit_summary


def generate_proof_for_epoch(epoch_id: str) -> ContinuityProof:
    summary = build_cockpit_summary(epoch_id=epoch_id)
    return proof_from_cockpit_summary(epoch_id, summary)
