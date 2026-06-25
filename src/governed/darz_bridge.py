"""DAR-Z metadata and receipt construction for governed missions."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from src.darz_kernel_bridge import (
    DarzBridgeInput,
    DarzNodeAdvertisement,
    build_darz_bridge_receipt,
    darz_bridge_summary,
)

from src.governed.config import GovernedRuntimeConfig, get_governed_config
from src.governed.t5_bridge import attach_t5_references


def _boundary(cfg: GovernedRuntimeConfig | None) -> GovernedRuntimeConfig:
    return cfg or get_governed_config()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def build_darz_metadata(law_eval: dict[str, Any]) -> dict[str, Any]:
    """Metadata attached to URG mission context before execution."""
    law_eval_id = str(law_eval.get("id") or "")
    return {
        "law_eval_id": law_eval_id,
        "intent": str(law_eval.get("intent") or "governed_constitutional_spine"),
        "t5_refs": attach_t5_references(law_eval),
        "governed": True,
        "bridge_version": "darz.kernel.bridge.v0.1",
    }


def build_darz_receipt_from_urg(
    *,
    law_eval: dict[str, Any],
    urg_receipt: dict[str, Any],
    steward_identity: dict[str, Any],
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Convert URG mission receipt into a DAR-Z bridge receipt for AAES."""
    cfg = _boundary(config)
    mission_id = str(urg_receipt.get("mission_id") or "")
    law_eval_id = str(law_eval.get("id") or "")
    trace_hash = _digest(f"{mission_id}:{law_eval_id}")
    schema = dict(urg_receipt.get("mission_receipt_schema") or {})
    receipt = build_darz_bridge_receipt(
        DarzBridgeInput(
            ugr_trace_id=mission_id or law_eval_id,
            ugr_proof_id=str(schema.get("receipt_id") or law_eval_id),
            ugr_proof_status="PROVEN" if urg_receipt.get("status") == "ok" else "PENDING",
            ugr_cvr_id=law_eval_id,
            ugr_cvr_score=1.0 if urg_receipt.get("status") == "ok" else 0.0,
            ugr_trace_hash=trace_hash,
            ugr_replay_hash=trace_hash,
            aais_status=str(urg_receipt.get("status") or "unknown"),
            aais_trace_stages=["governed_mission", "lawful_nova", "urg_mission"],
            tri_core_authority=cfg.tri_core_routing_authority,
            active_runtimes=["lawful_nova", "urg", "aaes"],
            darz_node=DarzNodeAdvertisement(
                node_id="darz.node.governed-mission",
                status="ACTIVE",
                threads=3,
                events=3,
                reconstruction="PASS",
                proof_status="PROVEN",
                federation_ready=True,
                genesis_threads=("founder.genesis", "identity.genesis", "darz.genesis"),
                proof_hash="darz.node.governed-mission.proof",
            ),
            timestamp=_now(),
            thread_label=f"governed:{steward_identity.get('steward_id', 'operator')}",
        )
    )
    return {
        "receipt": receipt,
        "summary": darz_bridge_summary(receipt),
    }
