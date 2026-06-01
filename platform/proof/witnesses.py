"""Global proof network witnesses (v43–v44)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore

WITNESS_VERSION = "platform.proof_witness.v1"


def enroll_witness(
    *,
    store: PlatformStore,
    witness_id: str,
    region: str = "us",
    public_key_ref: str = "",
) -> dict[str, Any]:
    payload = {
        "witness_version": WITNESS_VERSION,
        "witness_id": witness_id,
        "region": region,
        "public_key_ref": public_key_ref,
        "status": "active",
        "enrolled_at": datetime.now(UTC).isoformat(),
    }
    return store.upsert_proof_witness(payload)


def list_witnesses(*, store: PlatformStore) -> list[dict[str, Any]]:
    return store.list_proof_witnesses()


def witness_quorum_required() -> int:
    return int(os.environ.get("PLATFORM_WITNESS_QUORUM", "0"))


def witness_required() -> bool:
    return os.environ.get("PLATFORM_WITNESS_REQUIRED", "0") == "1"


def effective_witness_quorum() -> int:
    wq = witness_quorum_required()
    if witness_required():
        return max(1, wq)
    return wq


def witness_policy_satisfied(*, store: PlatformStore, job_id: str) -> bool:
    need = effective_witness_quorum()
    if need <= 0:
        return True
    return count_witness_attestations(store=store, job_id=job_id) >= need


def count_witness_attestations(*, store: PlatformStore, job_id: str) -> int:
    n = 0
    for att in store.list_attestations(job_id=job_id):
        if att.get("witness_id") or str(att.get("runner_id", "")).startswith("witness:"):
            n += 1
    return n


def build_proof_graph(*, store: PlatformStore, job_id: str) -> dict[str, Any]:
    job = store.get_job(job_id)
    attestations = store.list_attestations(job_id=job_id)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()
    for att in attestations:
        rid = str(att.get("runner_id") or "")
        if rid not in seen:
            seen.add(rid)
            nodes.append({"id": rid, "type": "runner"})
        edges.append(
            {
                "from": rid,
                "to": str(att.get("result_hash") or "")[:16],
                "attestation_id": att.get("attestation_id"),
            }
        )
    for w in store.list_proof_witnesses():
        wid = str(w.get("witness_id"))
        nodes.append({"id": wid, "type": "witness"})
    return {
        "job_id": job_id,
        "proof_status": (job or {}).get("proof_status"),
        "nodes": nodes,
        "edges": edges,
        "witness_count": count_witness_attestations(store=store, job_id=job_id),
        "witness_quorum_required": witness_quorum_required(),
    }
