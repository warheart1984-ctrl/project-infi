"""Attestation bundle export (v36)."""

from __future__ import annotations

from typing import Any

from platform.proof.federation import federation_status
from platform.store import PlatformStore

BUNDLE_VERSION = "platform.proof_attestation_bundle.v1"


def build_attestation_bundle(*, store: PlatformStore, job_id: str) -> dict[str, Any]:
    job = store.get_job(job_id)
    if not job:
        raise ValueError("job not found")
    status = federation_status(store=store, job=job)
    claim = "proven" if status.get("quorum_met") else "asserted"
    if status.get("hash_mismatch"):
        claim = "rejected"
    return {
        "bundle_version": BUNDLE_VERSION,
        "job_id": job_id,
        "federation_status": status,
        "attestations": status.get("attestations") or [],
        "claim_label": claim,
    }
