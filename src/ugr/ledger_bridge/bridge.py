"""LedgerBridge governed traverse gate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from src.ugr.ledger_bridge.invariants import BridgeInvariantError, validate_bridge_invariants
from src.ugr.ledger_bridge.trace import BridgeTraceLog

MLCALane = Literal["SAFE", "NORMAL", "EXPRESS"]


@dataclass
class LedgerClaim:
    claim_id: str
    law_id: str
    law_version: str
    sigil: str
    source_node: str = ""
    tenant_scope: str = "global"
    payload: dict[str, Any] = field(default_factory=dict)
    sigil_source: str = "ledger"
    law_clearance_token: str = ""
    human_explicit: bool = False
    constraint_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "law_id": self.law_id,
            "law_version": self.law_version,
            "sigil": self.sigil,
            "source_node": self.source_node,
            "tenant_scope": self.tenant_scope,
            "payload": self.payload,
            "sigil_source": self.sigil_source,
            "law_clearance_token": self.law_clearance_token,
            "human_explicit": self.human_explicit,
            "constraint_nodes": list(self.constraint_nodes),
        }


@dataclass
class BridgeResult:
    claim_id: str
    claim_label: str
    status: str
    bridge_trace_id: str
    lane: str
    diagnostic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_label": self.claim_label,
            "status": self.status,
            "bridge_trace_id": self.bridge_trace_id,
            "lane": self.lane,
            "diagnostic": self.diagnostic,
        }


class LedgerBridge:
    """Validate/emit only — no Stage 3 apply (MA-13 Class III)."""

    def __init__(
        self,
        *,
        trust_organ: Any,
        trace_path: str | Path,
        runtime_root: str | Path | None = None,
    ) -> None:
        self.trust_organ = trust_organ
        self.trace = BridgeTraceLog(Path(trace_path))
        self._seen: set[str] = set()
        self._runtime_root = Path(runtime_root or ".runtime")

    def traverse(
        self,
        claim: LedgerClaim | dict[str, Any],
        *,
        lane: MLCALane = "NORMAL",
        session_id: str,
        law_id: str,
        law_version: str,
    ) -> BridgeResult:
        body = claim.to_dict() if isinstance(claim, LedgerClaim) else dict(claim)
        cid = str(body.get("claim_id") or uuid.uuid4())
        body["claim_id"] = cid
        try:
            validate_bridge_invariants(
                claim=body,
                lane=lane,
                session_id=session_id,
                law_id=law_id,
                law_version=law_version,
                seen_claim_ids=self._seen,
            )
            if not body.get("human_explicit") and body.get("binding_goal"):
                raise BridgeInvariantError("GOV-03", "binding goal without human_explicit")
            if body.get("drops_constraints"):
                raise BridgeInvariantError("GOV-02", "constraint nodes dropped")
            trace_entry = self.trace.append(
                {
                    "claim_id": cid,
                    "session_id": session_id,
                    "lane": lane,
                    "law_id": law_id,
                    "law_version": law_version,
                    "stage": "validated",
                    "claim_label": "asserted",
                }
            )
            self._seen.add(cid)
            receipt = self.trust_organ.receive_claim(body, bridge_trace=trace_entry)
            if not receipt.get("acknowledged"):
                raise BridgeInvariantError("GOV-08", "trust bundle organ did not acknowledge")
            final_trace = self.trace.append(
                {
                    "claim_id": cid,
                    "session_id": session_id,
                    "lane": lane,
                    "stage": "elevated",
                    "claim_label": "proven",
                    "trust_receipt_id": receipt.get("receipt_id"),
                }
            )
            return BridgeResult(
                claim_id=cid,
                claim_label="proven",
                status="elevated",
                bridge_trace_id=str(final_trace.get("trace_id")),
                lane=lane,
            )
        except BridgeInvariantError as exc:
            self.trace.append(
                {
                    "claim_id": cid,
                    "session_id": session_id,
                    "lane": lane,
                    "stage": "blocked",
                    "claim_label": "asserted",
                    "diagnostic": str(exc),
                }
            )
            return BridgeResult(
                claim_id=cid,
                claim_label="asserted",
                status="blocked",
                bridge_trace_id="",
                lane=lane,
                diagnostic=str(exc),
            )

    def query_trace(self, claim_id: str) -> list[dict[str, Any]]:
        return self.trace.query(claim_id)
