"""Subsystem discovery receipt v1 — hash-anchored proof of valid spec."""

# Engineering: SubsystemDiscoveryReceiptEngine
from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from src.ugr.discovery.subsystem_spec import SubsystemSpec, stable_json, subsystem_id_from_spec
from src.ugr.discovery.subsystem_validity import ValidityResult
from src.ugr.mission.receipt_signing import load_urg_receipt_signing_key, sign_urg_receipt


DISCOVERY_RECEIPT_SCHEMA_VERSION = "1.0"


def build_discovery_receipt_canonical(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_schema_version": receipt.get("receipt_schema_version"),
        "subsystem_id": receipt.get("subsystem_id"),
        "spec": receipt.get("spec"),
        "invariants_passed": receipt.get("invariants_passed"),
        "organs_matched": receipt.get("organs_matched"),
        "rail_proof": receipt.get("rail_proof"),
        "law_version": receipt.get("law_version"),
        "tenant_id": receipt.get("tenant_id"),
        "operator_id": receipt.get("operator_id"),
        "aais_instance_id": receipt.get("aais_instance_id"),
        "discovered_at": receipt.get("discovered_at"),
        "discovery_mode": receipt.get("discovery_mode"),
        "search_attempts": receipt.get("search_attempts"),
    }


def build_subsystem_discovery_receipt(
    spec: SubsystemSpec,
    validity: ValidityResult,
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
    sid = subsystem_id_from_spec(spec)
    rail_proof = dict(validity.rail_proof or {})
    receipt: dict[str, Any] = {
        "receipt_schema_version": DISCOVERY_RECEIPT_SCHEMA_VERSION,
        "receipt_id": str(uuid4()),
        "subsystem_id": sid,
        "spec": spec.canonical_dict(),
        "invariants_passed": list(validity.invariants),
        "organs_matched": list(validity.organs_matched),
        "rail_proof": {
            "requested": rail_proof.get("requested"),
            "scheduled": rail_proof.get("scheduled"),
            "codes": list(rail_proof.get("codes") or []),
        },
        "law_version": {
            "law_id": rail_proof.get("law_id"),
            "law_version": rail_proof.get("law_version"),
        },
        "genome_metadata": dict(validity.genome_metadata or {}),
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "aais_instance_id": aais_instance_id,
        "discovered_at": time.time(),
        "discovery_mode": discovery_mode,
        "search_attempts": int(search_attempts),
        "search_trail": list(search_trail or [])[-8:],
        "catalog_status": "shadow",
    }
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


def verify_subsystem_discovery_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[bool, str]:
    from hashlib import sha256
    import hmac

    from src.ugr.mission.receipt_signing import (
        ALGORITHM_CONTENT_ONLY,
        ALGORITHM_HMAC,
        build_urg_receipt_canonical,
        load_urg_receipt_signing_key,
    )

    canonical = stable_json(build_urg_receipt_canonical(receipt))
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
