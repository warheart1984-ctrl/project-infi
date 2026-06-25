"""Full constitutional spine: Lawful Nova → URG → AAES → Nexus OS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from nova.bridges import identity_bridge

from src.governed.aaes_bridge import send_to_aaes
from src.governed.config import GovernedRuntimeConfig, get_governed_config
from src.governed.nexus_bridge import emit_nexus_event
from src.governed.nova_bridge import call_lawful_nova
from src.governed.persistence import persist_panels_and_receipts
from src.governed.t5_bridge import attach_t5_references
from src.governed.urg_bridge import build_and_send_urg_mission


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_steward_identity(steward_identity: dict[str, Any] | None) -> dict[str, Any]:
    if steward_identity:
        return dict(steward_identity)
    snapshot = identity_bridge.get_current_identity()
    identity = dict(snapshot.identity)
    identity.setdefault("steward_id", identity.get("operator_id") or "operator")
    identity["epoch"] = snapshot.epoch
    return identity


def make_governed_mission(
    user_turn: str,
    steward_identity: dict[str, Any] | None = None,
    *,
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """
    Full constitutional spine:
    Nova → URG → AAES → Nexus OS

    Returns a complete constitutional trace.
    """
    cfg = config or get_governed_config()
    steward = _resolve_steward_identity(steward_identity)
    started_at = _now()

    law_eval = call_lawful_nova(text=user_turn, steward_identity=steward, config=cfg)
    urg_receipt = build_and_send_urg_mission(
        law_eval=law_eval,
        steward_identity=steward,
        user_text=user_turn,
        config=cfg,
    )
    aaes_receipt = send_to_aaes(
        law_eval=law_eval,
        urg_receipt=urg_receipt,
        steward_identity=steward,
        user_text=user_turn,
        config=cfg,
    )
    nexus_event = emit_nexus_event(aaes_receipt, config=cfg)
    persistence = persist_panels_and_receipts(
        law_eval=law_eval,
        urg_receipt=urg_receipt,
        aaes_receipt=aaes_receipt,
        nexus_event=nexus_event,
        config=cfg,
    )

    spine_ok = (
        law_eval.get("status") == "ok"
        and urg_receipt.get("status") == "ok"
        and aaes_receipt.get("executed")
    )

    return {
        "status": "ok" if spine_ok else "partial",
        "started_at": started_at,
        "completed_at": _now(),
        "law_eval": law_eval,
        "urg_receipt": urg_receipt,
        "aaes_receipt": aaes_receipt,
        "nexus_event": nexus_event,
        "constitutional_trace": {
            "panels": persistence["panels"],
            "references": attach_t5_references(law_eval),
            "hashes": {
                "law_eval": law_eval.get("law_hash"),
                "darz_bridge": aaes_receipt.get("darz_bridge_hash"),
                "urg_mission": str(urg_receipt.get("urg_ingress", {}).get("stamp_hash") or ""),
            },
            "timestamps": {
                "started_at": started_at,
                "completed_at": _now(),
                "nexus_recorded_at": nexus_event.get("recorded_at"),
            },
            "persistence": persistence,
            "steward_identity": steward,
        },
    }
