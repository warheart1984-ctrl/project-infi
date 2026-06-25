#!/usr/bin/env python3
"""
Alpha Proof Script:
AuditRecord → PELRecord → Claim → VerificationRecord → Verified Claim

Requires a running AAIS/runtime at RUNTIME_BASE_URL (default http://localhost:8000).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.pel.bootstrap_claims import create_alpha_t1_claim  # noqa: E402
from src.cori.pel.models import Claim, PELRecord, VerificationRecord  # noqa: E402
from src.cori.pel.pel_register import audit_to_pel, fetch_audit_record, runtime_base_url  # noqa: E402
from src.cori.pel.pel_verify import verify_pel_record  # noqa: E402
from src.cori.pel.storage import ClaimStorage, PelStorage, VerificationStorage  # noqa: E402


def core_loop_payload() -> dict[str, Any]:
    return {
        "email": "alpha-proof@example.org",
        "display_name": "Alpha Proof User",
        "asset": {
            "type": "document",
            "name": "Alpha Proof Asset",
            "metadata": {"category": "alpha-proof"},
        },
        "evidence": {
            "kind": "upload",
            "uri": "s3://alpha-proof/bucket/artifact",
            "hash": "alpha-proof-hash",
        },
    }


def run_core_loop(
    *,
    base_url: str | None = None,
    client: httpx.Client | None = None,
) -> str:
    """Call runtime core-loop and return audit_id."""
    payload = core_loop_payload()
    url_base = (base_url or runtime_base_url()).rstrip("/")

    if client is not None:
        response = client.post("/v1/runtime/core-loop", json=payload)
        response.raise_for_status()
        return str(response.json()["audit_id"])

    with httpx.Client(base_url=url_base, timeout=10.0) as http:
        response = http.post("/v1/runtime/core-loop", json=payload)
        response.raise_for_status()
        return str(response.json()["audit_id"])


def run_alpha_proof(
    *,
    base_url: str | None = None,
    client: httpx.Client | None = None,
    persist: bool = True,
) -> tuple[str, PELRecord, Claim, VerificationRecord]:
    """
    Full governance proof chain. Returns (audit_id, pel, claim, verification).
    """
    audit_id = run_core_loop(base_url=base_url, client=client)
    audit = fetch_audit_record(audit_id, base_url=base_url, client=client)
    pel_record = audit_to_pel(audit)
    claim = create_alpha_t1_claim()
    verification = verify_pel_record(pel_record, claim)

    if persist:
        PelStorage().save_pel_record(pel_record)
        ClaimStorage().save_claim(claim)
        VerificationStorage().save_verification(verification)

    return audit_id, pel_record, claim, verification


def main() -> int:
    print("=== CORI Alpha – Tier-1 Governance Proof ===")

    print("[1] Running runtime core loop...")
    audit_id, pel_record, claim, verification = run_alpha_proof(persist=True)
    print(f"    ✓ Got audit_id: {audit_id}")

    print("[2] AuditRecord loaded from runtime")
    print(f"    ✓ decision={pel_record.decision}")

    print("[3] Converted AuditRecord → PELRecord")
    print(f"    ✓ PELRecord id={pel_record.id} primary_hash={pel_record.primary_hash}")

    print("[4] Tier-1 governance Claim")
    print(f"    ✓ Claim id={claim.id}")

    print("[5] Verification")
    print(f"    ✓ status={verification.status}")

    if verification.status == "verified":
        print("\n=== RESULT: Tier-1 governance proof PASSED ===")
        print("An independent observer can:")
        print(f"- Start from Claim: {claim.id}")
        print(f"- Traverse to PELRecord: {pel_record.id}")
        print(f"- Traverse to AuditRecord: {audit_id}")
        print("- Recompute the canonical hash and confirm the invariant holds.")
        return 0

    print("\n=== RESULT: Tier-1 governance proof FAILED ===")
    print("Details:", verification.details)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Alpha proof script failed:", exc, file=sys.stderr)
        raise SystemExit(1) from exc
