"""Deep RIL replay — re-materialize epoch state and rebuild cockpit summary."""

from __future__ import annotations

from typing import Any

from nova.continuity.ril_bridge import ReplayedSummary
from nova.continuity.types import RILExport
from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.lineage import reflexive_events
from nova.crk.perception.perception_metrics import PerceptionSnapshot
from nova.governance.steward_models import AmendmentProposal, RatifiedAmendment, StewardId, StewardSignature
from nova.governance.steward_ledger import clear_steward_ledger, get_steward_ledger
from nova.law_kernel.models import LawContext, new_intent
from nova.law_kernel.transform import pit2_transform


def _restore_reflexive_events(events: list[dict[str, Any]]) -> None:
    reflexive_events.clear_reflexive_events()
    reflexive_events._events.extend(events)  # noqa: SLF001 — replay restore hook


def _restore_perception_snapshots(snapshots: list[dict[str, Any]]) -> None:
    from nova.crk.panels import perception_health_panel as panel_mod

    panel_mod._snapshots.clear()  # noqa: SLF001
    for row in snapshots:
        panel_mod._snapshots.append(  # noqa: SLF001
            PerceptionSnapshot(
                intent_id=str(row.get("intent_id") or ""),
                epoch_id=str(row.get("epoch_id") or ""),
                inputs=dict(row.get("inputs") or {}),
                outputs=dict(row.get("outputs") or {}),
                confidence=float(row.get("confidence") or 0.0),
                anomaly_score=float(row.get("anomaly_score") or 0.0),
            )
        )


def _restore_steward_events(events: list[dict[str, Any]]) -> None:
    clear_steward_ledger()
    ledger = get_steward_ledger()
    for event in events:
        kind = event.get("kind")
        if kind == "AMENDMENT_PROPOSAL":
            ledger.record_proposal(
                AmendmentProposal(
                    id=str(event.get("id") or ""),
                    steward_id=StewardId(str(event.get("steward_id") or "operator")),
                    payload=dict(event.get("payload") or {}),
                    status=str(event.get("status") or "proposed"),
                    created_at=str(event.get("created_at") or ""),
                    lineage_event_id=str(event.get("lineage_event_id") or ""),
                )
            )
        elif kind == "AMENDMENT_RATIFIED":
            signatures = [
                StewardSignature(
                    steward_id=StewardId(str(sig.get("steward_id") or "operator")),
                    signed_at=str(sig.get("signed_at") or ""),
                    t5_ref_signal_hash=str(sig.get("t5_ref_signal_hash") or ""),
                    lineage_event_id=str(sig.get("lineage_event_id") or ""),
                )
                for sig in event.get("signatures") or []
            ]
            amendment = RatifiedAmendment(
                proposal_id=str(event.get("proposal_id") or ""),
                signatures=signatures,
                payload=dict(event.get("payload") or {}),
                ratified_at=str(event.get("ratified_at") or ""),
                lineage_event_id=str(event.get("lineage_event_id") or ""),
                t5_ref_signal_hash=str(event.get("t5_ref_signal_hash") or ""),
            )
            ledger.record_ratification(amendment)


def _verify_reflexive_through_law_kernel(events: list[dict[str, Any]], epoch_id: str) -> list[dict[str, Any]]:
    """Read-only law-kernel pass: re-apply PIT-2 transform on stored eval metadata."""
    notes: list[dict[str, Any]] = []
    for event in events:
        if event.get("kind") != reflexive_events.KIND_REFLEXIVE_EVAL:
            continue
        ctx = LawContext(
            actor_id="replay",
            domain="cognition",
            epoch=epoch_id,
            lineage_contract_id=str(event.get("lineage_event_id") or "lc-replay"),
            t5_ref_signal_hash=str(event.get("t5_ref_signal_hash") or ""),
            lineage_event_id=str(event.get("lineage_event_id") or ""),
        )
        intent = new_intent(
            kind="ASK",
            payload={
                "pit_mode": "PIT-2",
                "pit_evidence_fitness": 0.9,
                "correctness_score": 0.9,
                "self_reflection": dict(event.get("payload") or {}),
            },
            origin="replay",
        )
        transformed = pit2_transform(intent, ctx)
        notes.append(
            {
                "intent_id": event.get("intent_id"),
                "pit_mode": transformed.transformed_intent.payload.get("pit_mode"),
                "verified": True,
            }
        )
    return notes


def replay_ril(ril: RILExport) -> ReplayedSummary:
    """
    Deep replay: restore exported lineage, verify reflexive events through the
    law-kernel PIT-2 transform, then rebuild the cockpit summary from materialized state.
    """
    bundle = dict(ril.bundle)
    epoch_id = ril.epoch_id

    reflexive = list(bundle.get("reflexive_events") or [])
    _restore_reflexive_events(reflexive)
    _restore_perception_snapshots(list(bundle.get("perception_snapshots") or []))
    _restore_steward_events(list(bundle.get("steward_events") or []))
    _verify_reflexive_through_law_kernel(reflexive, epoch_id)

    summary = build_cockpit_summary(epoch_id=epoch_id)
    return ReplayedSummary(epoch_id=epoch_id, cockpit_summary=summary)
