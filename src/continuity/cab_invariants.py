"""CAB invariants — reconstructability, causal linkage, temporal integrity, succession, non-erasure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.cab import CABLedger, CABObjectType


@dataclass(frozen=True)
class InvariantResult:
    invariant_id: str
    name: str
    status: str
    detail: str = ""


@dataclass
class CABInvariantReport:
    results: list[InvariantResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.status == "pass" for result in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "results": [
                {
                    "invariant_id": result.invariant_id,
                    "name": result.name,
                    "status": result.status,
                    "detail": result.detail,
                }
                for result in self.results
            ],
        }


def _active_by_type(ledger: CABLedger, object_type: CABObjectType) -> list[dict[str, Any]]:
    return [entry.payload for entry in ledger.list_by_type(object_type)]


def _ref_exists(active_ids: set[str], ref: str) -> bool:
    return ref in active_ids


def evaluate_cab_invariants(ledger: CABLedger) -> CABInvariantReport:
    report = CABInvariantReport()
    active = ledger.active_payloads()
    active_ids = set(active.keys())

    # CL — Causal linkage: decisions link to intents
    decisions = _active_by_type(ledger, CABObjectType.DECISION)
    orphan_decisions = [
        payload["decision_id"]
        for payload in decisions
        if not payload.get("intent_refs")
        or not all(_ref_exists(active_ids, ref) for ref in payload["intent_refs"])
    ]
    report.results.append(
        InvariantResult(
            invariant_id="CL",
            name="causal_linkage",
            status="pass" if not orphan_decisions else "fail",
            detail="" if not orphan_decisions else f"orphan or unlinked decisions: {orphan_decisions}",
        )
    )

    # RC — Reconstructability: plan references reachable objects
    plans = _active_by_type(ledger, CABObjectType.RECONSTRUCTION)
    rc_failures: list[str] = []
    for plan in plans:
        missing = [ref for ref in plan.get("minimal_object_refs") or [] if not _ref_exists(active_ids, ref)]
        if missing:
            rc_failures.append(f"{plan['plan_id']}: missing {missing}")
    report.results.append(
        InvariantResult(
            invariant_id="RC",
            name="reconstructability",
            status="pass" if not rc_failures else "fail",
            detail="; ".join(rc_failures),
        )
    )

    # TI — Temporal integrity: monotonic sequence and non-decreasing created_at
    sequences = [entry.sequence for entry in ledger.entries]
    ti_ok = sequences == list(range(1, len(sequences) + 1))
    timestamps = [entry.created_at for entry in ledger.entries]
    ti_ok = ti_ok and timestamps == sorted(timestamps)
    report.results.append(
        InvariantResult(
            invariant_id="TI",
            name="temporal_integrity",
            status="pass" if ti_ok else "fail",
            detail="" if ti_ok else "sequence or timestamp order violated",
        )
    )

    # SU — Succession: founder snapshots with succession notes should reference a protocol
    protocols = {payload["protocol_id"] for payload in _active_by_type(ledger, CABObjectType.SUCCESSION)}
    founder = _active_by_type(ledger, CABObjectType.FOUNDER_KNOWLEDGE)
    su_failures: list[str] = []
    for snapshot in founder:
        notes = str(snapshot.get("succession_notes") or "").strip()
        if notes and not protocols:
            su_failures.append(snapshot["snapshot_id"])
    report.results.append(
        InvariantResult(
            invariant_id="SU",
            name="succession",
            status="pass" if not su_failures else "fail",
            detail="" if not su_failures else f"snapshots without protocol: {su_failures}",
        )
    )

    # NE — Non-erasure: ledger only grows; supersede marks present, no deletes
    ne_ok = len(ledger.entries) >= len(active_ids)
    for entry in ledger.entries:
        if entry.superseded and not entry.payload.get("superseded_by"):
            ne_ok = False
            break
    report.results.append(
        InvariantResult(
            invariant_id="NE",
            name="non_erasure",
            status="pass" if ne_ok else "fail",
            detail="" if ne_ok else "superseded entry missing superseded_by link",
        )
    )

    return report
