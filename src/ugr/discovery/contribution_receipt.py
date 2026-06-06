"""Contribution discovery receipt v1 — hash-anchored proof of valid contribution."""

# Mythic: Contribution Receipt
# Engineering: ContributionReceiptEngine
from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from src.ugr.discovery.contribution_spec import ContributionSpec, stable_json
from src.ugr.mission.receipt_signing import load_urg_receipt_signing_key, sign_urg_receipt


DISCOVERY_RECEIPT_SCHEMA_VERSION = "1.1"


def build_contribution_receipt_canonical(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_schema_version": receipt.get("receipt_schema_version"),
        "contribution_id": receipt.get("contribution_id"),
        "contribution_type": receipt.get("contribution_type"),
        "payload": receipt.get("payload"),
        "invariants_passed": receipt.get("invariants_passed"),
        "proof": receipt.get("proof"),
        "law_version": receipt.get("law_version"),
        "tenant_id": receipt.get("tenant_id"),
        "operator_id": receipt.get("operator_id"),
        "aais_instance_id": receipt.get("aais_instance_id"),
        "discovered_at": receipt.get("discovered_at"),
        "discovery_mode": receipt.get("discovery_mode"),
    }


def build_contribution_discovery_receipt(
    spec: ContributionSpec,
    validity: Any,
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    discovery_mode: str = "validate",
    search_attempts: int = 0,
    search_trail: list[dict[str, Any]] | None = None,
    runtime_dir: str | None = None,
    create_key_if_missing: bool = True,
) -> dict[str, Any]:
    cid = spec.contribution_id()
    proof = dict(getattr(validity, "proof", None) or getattr(validity, "rail_proof", None) or {})
    receipt: dict[str, Any] = {
        "receipt_schema_version": DISCOVERY_RECEIPT_SCHEMA_VERSION,
        "receipt_id": str(uuid4()),
        "contribution_id": cid,
        "contribution_type": spec.contribution_type,
        "payload": dict(spec.payload),
        "invariants_passed": list(getattr(validity, "invariants", None) or []),
        "proof": proof,
        "law_version": proof.get("law_version") or proof.get("law_id"),
        "genome_metadata": dict(getattr(validity, "genome_metadata", None) or {}),
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "aais_instance_id": aais_instance_id,
        "discovered_at": time.time(),
        "discovery_mode": discovery_mode,
        "search_attempts": int(search_attempts),
        "search_trail": list(search_trail or [])[-8:],
        "catalog_status": "shadow",
    }
    if spec.contribution_type == "subsystem":
        receipt["subsystem_id"] = cid
        receipt["spec"] = dict(spec.payload)
        receipt["organs_matched"] = list(getattr(validity, "organs_matched", None) or [])
        receipt["rail_proof"] = proof

    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if urg_key_id:
        receipt["urg_key_id"] = urg_key_id
    receipt_sig, algorithm, _ = sign_urg_receipt(
        receipt,
        runtime_dir=runtime_dir,
        create_key_if_missing=create_key_if_missing,
    )
    receipt["receipt_sig"] = receipt_sig
    receipt["receipt_algorithm"] = algorithm
    return receipt


def verify_contribution_discovery_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[bool, str]:
    from hashlib import sha256
    import hmac

    from src.ugr.mission.receipt_signing import (
        ALGORITHM_CONTENT_ONLY,
        ALGORITHM_HMAC,
        load_urg_receipt_signing_key,
    )

    canonical = stable_json(build_contribution_receipt_canonical(receipt))
    sig = str(receipt.get("receipt_sig") or "")
    algorithm = str(receipt.get("receipt_algorithm") or ALGORITHM_CONTENT_ONLY)
    key, _ = load_urg_receipt_signing_key(runtime_dir=runtime_dir, create_if_missing=False)
    if algorithm == ALGORITHM_HMAC and key:
        expected = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        if hmac.compare_digest(expected, sig):
            return True, "ok"
        return False, "receipt_sig mismatch"
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if hmac.compare_digest(expected, sig):
        return True, "ok"
    return False, "receipt_sig mismatch"
