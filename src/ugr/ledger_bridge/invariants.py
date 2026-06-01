"""Bridge invariant surface INV-BRIDGE-01..08."""

from __future__ import annotations

from typing import Any


class BridgeInvariantError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def validate_bridge_invariants(
    *,
    claim: dict[str, Any],
    lane: str,
    session_id: str,
    law_id: str,
    law_version: str,
    seen_claim_ids: set[str] | None = None,
) -> None:
    if not law_id or claim.get("law_id") != law_id:
        raise BridgeInvariantError("GOV-01", "claim.law_id must match session law bundle")
    cv = str(claim.get("law_version") or "")
    if law_version and cv and cv != law_version:
        raise BridgeInvariantError("GOV-02", "claim.law_version mismatch")
    if not claim.get("sigil"):
        raise BridgeInvariantError("GOV-03", "claim must carry sigil")
    if claim.get("sigil_source") == "caller_supplied":
        raise BridgeInvariantError("GOV-03", "sigil must not be caller-supplied only")
    if not claim.get("source_node") and not claim.get("claim_id"):
        raise BridgeInvariantError("GOV-12", "claim must be traceable to ledger node")
    cid = str(claim.get("claim_id") or "")
    if seen_claim_ids is not None and cid and cid in seen_claim_ids:
        raise BridgeInvariantError("RNT-04", "duplicate traverse for claim_id")
    if lane == "EXPRESS" and not claim.get("law_clearance_token"):
        raise BridgeInvariantError("GOV-06", "EXPRESS lane requires law_clearance_token")
    if lane not in {"SAFE", "NORMAL", "EXPRESS"}:
        raise BridgeInvariantError("GOV-06", f"unknown lane {lane}")
