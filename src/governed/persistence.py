"""Step 5 — Write-through persistence for panels, receipts, and continuity evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from nova.bridges import identity_bridge, law_ledger_bridge, panel_store
from nova.law_kernel.types import LawEvent

from src.aaes_os.nexus_execution_ledger import get_nexus_execution_ledger
from src.continuity.continuity_store import get_continuity_store
from src.continuity.law_ledger import default_law_ledger_path
from src.cori.evidence_factory import EvidenceFactory, get_evidence_factory
from src.governed.adapters import get_nexusos_continuity_adapter
from src.governed.config import GovernedRuntimeConfig, get_governed_config


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def persist_panels_and_receipts(
    *,
    law_eval: dict[str, Any],
    urg_receipt: dict[str, Any],
    aaes_receipt: dict[str, Any],
    nexus_event: dict[str, Any],
    evidence: EvidenceFactory | None = None,
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Persist governed mission evidence into SQLite-backed stores."""
    cfg = config or get_governed_config()
    factory = evidence or get_evidence_factory()
    store = panel_store.get_panel_store()
    continuity = get_continuity_store()
    identity = identity_bridge.get_current_identity()
    steward_id = str(
        identity.identity.get("steward_id")
        or identity.identity.get("operator_id")
        or "operator"
    )

    law_eval_id = str(law_eval.get("id") or "")
    mission_id = str(urg_receipt.get("mission_id") or "")
    execution_id = str(aaes_receipt.get("execution_id") or aaes_receipt.get("trace_id") or "")
    asset_id = f"asset:mission:{mission_id}" if mission_id else f"asset:law:{law_eval_id}"

    factory.emit_identity_snapshot(steward_id, identity.identity)

    factory.emit_asset_created(
        asset_id,
        {
            "asset_type": "governed_mission",
            "mission_id": mission_id,
            "law_eval_id": law_eval_id,
            "user_intent": law_eval.get("intent"),
        },
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
    )

    factory.emit_evidence_attached(
        asset_id=asset_id,
        artifact={
            "kind": "law_eval_artifact",
            "law_eval": law_eval,
            "law_hash": law_eval.get("law_hash"),
        },
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        mission_id=mission_id,
    )

    decision = "admitted" if law_eval.get("status") == "ok" else "denied"
    _requested, validation_decided = factory.emit_validation(
        asset_id=asset_id,
        law_eval_id=law_eval_id,
        decision=decision,
        steward_identity=steward_id,
        mission_id=mission_id,
        details={"law_status": law_eval.get("status")},
    )

    urg_body = dict(urg_receipt)
    urg_body["law_eval_id"] = law_eval_id
    urg_body["governed"] = True
    factory.emit_law_eval(law_eval, steward_identity=steward_id, asset_id=asset_id, introduced_by="nova")
    factory.emit_urg_mission(
        urg_body,
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        asset_id=asset_id,
        governed=True,
    )

    aaes_body = dict(aaes_receipt)
    aaes_body["law_eval_id"] = law_eval_id
    aaes_body["mission_id"] = mission_id
    aaes_body["validation_evidence_id"] = validation_decided.evidence_id
    aaes_body["validation_id"] = validation_decided.evidence_id
    factory.emit_aaes_exec(
        aaes_body,
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        mission_id=mission_id,
        asset_id=asset_id,
    )

    nexus_body = dict(nexus_event)
    nexus_body["mission_id"] = mission_id
    factory.emit_nexus_event(
        nexus_body,
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        mission_id=mission_id,
        execution_id=execution_id,
        asset_id=asset_id,
    )

    reflexive_payload = {
        "kind": "governed_mission_complete",
        "epoch_id": identity.epoch,
        "intent_id": law_eval_id,
        "lineage_event_id": str(nexus_event.get("event_id") or nexus_event.get("recorded_at") or _now()),
        "t5_ref_signal_hash": str((law_eval.get("t5_refs") or {}).get("ref_hash") or ""),
        "steward_identity": steward_id,
        "payload": {
            "mission_id": mission_id,
            "aaes_trace_id": aaes_receipt.get("trace_id"),
            "execution_id": execution_id,
            "nexus_event_type": nexus_event.get("event_type"),
        },
        "timestamp": _now(),
    }
    store.append_reflexive_event(reflexive_payload)
    factory.emit_panel(
        "reflexive",
        reflexive_payload,
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        mission_id=mission_id,
        execution_id=execution_id,
    )

    steward_payload = {
        "law_eval_id": law_eval_id,
        "mission_id": mission_id,
        "urg_status": urg_receipt.get("status"),
        "aaes_status": aaes_receipt.get("status"),
        "darz_bridge_hash": aaes_receipt.get("darz_bridge_hash"),
        "execution_id": execution_id,
        "steward_id": steward_id,
        "recorded_at": _now(),
    }
    store.append_steward_event(kind="governed_mission_receipt", payload=steward_payload)
    factory.emit_panel(
        "steward",
        {"kind": "governed_mission_receipt", **steward_payload},
        steward_identity=steward_id,
        law_eval_id=law_eval_id,
        mission_id=mission_id,
        execution_id=execution_id,
    )

    law_ledger_bridge.record_law_event(
        LawEvent(
            entry_type="GOVERNED_MISSION",
            law_id="constitutional-spine",
            law_hash=str(aaes_receipt.get("darz_bridge_hash") or law_eval.get("law_hash") or ""),
            epoch=0,
            payload={
                "law_eval_id": law_eval_id,
                "mission_id": mission_id,
                "aaes_trace_id": aaes_receipt.get("trace_id"),
                "nexus_event_id": nexus_event.get("event_id"),
                "asset_id": asset_id,
            },
            signed_by="aais.governed_mission",
        )
    )

    ledger = get_nexus_execution_ledger()
    nexusos_export = None
    if cfg.nexusos_fos_export:
        nexusos_adapter = get_nexusos_continuity_adapter(True)
        nexusos_export = nexusos_adapter.export_mission_receipt(
            mission_id=mission_id,
            law_eval=law_eval,
            urg_receipt=urg_receipt,
            aaes_receipt=aaes_receipt,
            nexus_event=nexus_event,
        )
    unified_panels = store.list_panels()
    law_ledger_path = str(default_law_ledger_path())
    evidence_events = [
        e for e in continuity.list_events(limit=1000)
        if (e.get("event_type") or "").startswith(("evidence_", "validation_", "asset_", "identity_", "law_", "urg_", "aaes_", "nexus_", "panel_"))
    ]
    return {
        "panel_store_path": str(store.path),
        "continuity_store_path": str(continuity.path),
        "law_ledger_path": law_ledger_path,
        "asset_id": asset_id,
        "panels": {
            "unified": len(unified_panels),
            "reflexive": len(store.list_reflexive_events()),
            "steward": len(store.list_steward_events()),
            "perception": len(store.list_perception_snapshots()),
        },
        "continuity_events": len(continuity.list_events(limit=1000)),
        "evidence_events": len(evidence_events),
        "identity_snapshots": len(continuity.list_identity_snapshots(limit=1000)),
        "identity_epoch": identity.epoch,
        "identity_snapshot": identity.identity,
        "nexus_ledger_path": str(ledger.path),
        "nexus_execution_count": len(ledger.list_executions(limit=1000)),
        "nexusos_fos_export": nexusos_export,
        "spine_boundary": {
            "tri_core_routing_authority": cfg.tri_core_routing_authority,
            "aaes_execution_module_id": cfg.aaes_execution_module_id,
            "nexus_record_mode": cfg.nexus_record_mode,
            "nexusos_fos_export_enabled": cfg.nexusos_fos_export,
        },
        "law_ledger_cached_laws": len(law_ledger_bridge.list_cached_laws()),
        "persisted_at": _now(),
    }
