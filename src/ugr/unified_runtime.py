"""Unified Governed Runtime — bridge-first orchestration with MLCA v0."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from uuid import uuid4
import os

from src.cognitive_bridge import (
    DECISION_BLOCK,
    CognitiveBridgeService,
    summarize_bridge_result,
)
from src.jarvis_detachment_guard import build_bridge_attestation
from src.ugr.cloud_forge_bridge import (
    attach_cloud_forge_metadata,
    rail_trace_summary,
    resolve_tenant_manifold_for_forge,
    schedule_rail_for_ugr,
)
from src.ugr.embryo.model_pool import attach_model_pool_to_response
from src.ugr.convergence_engine import ConvergenceEngine
from src.ugr.lane_manager import LaneManager, design_lane_set, run_lanes
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.platform.tenant_registry import normalize_tenant_id


UGR_RUNTIME_ID = "aais.ugr.unified_runtime"
UGR_RUNTIME_VERSION = "0.1"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


class UnifiedGovernedRuntime:
    """Cloud-scale PID-1 skeleton — local single-node implementation."""

    def __init__(
        self,
        *,
        bridge: CognitiveBridgeService | None = None,
        ledger: PatternLedgerStore | None = None,
        lane_manager: LaneManager | None = None,
        convergence: ConvergenceEngine | None = None,
        runtime_dir: str | Path | None = None,
    ):
        root = Path(runtime_dir or _default_runtime_dir())
        self.runtime_dir = root / "ugr"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger or PatternLedgerStore(runtime_dir=root)
        self.bridge = bridge or CognitiveBridgeService()
        self.lane_manager = lane_manager or LaneManager(ledger=self.ledger)
        self.convergence = convergence or ConvergenceEngine()

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        root = Path(runtime_dir)
        self.runtime_dir = root / "ugr"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.ledger.configure_runtime_dir(root)

    @property
    def traces_path(self) -> Path:
        return self.runtime_dir / "traces.jsonl"

    def _append_trace(self, record: dict[str, Any]) -> None:
        self.traces_path.parent.mkdir(parents=True, exist_ok=True)
        with self.traces_path.open("a", encoding="utf-8") as handle:
            handle.write(_stable_json(record) + "\n")

    def _build_trace_id(self, request: dict[str, Any]) -> str:
        seed = _stable_json(
            {
                "question": request.get("question"),
                "intent": request.get("intent"),
                "tenant_id": request.get("tenant_id"),
            }
        )
        digest = sha256(seed.encode("utf-8")).hexdigest()[:12]
        return f"ugr-{digest}-{uuid4().hex[:8]}"

    def _append_ugr_trace(self, record: dict[str, Any], cloud_forge_bundle: dict[str, Any] | None) -> None:
        trace_record = dict(record)
        summary = rail_trace_summary(cloud_forge_bundle)
        if summary:
            trace_record["rail_decision"] = summary
        self._append_trace(trace_record)

    def _finalize_response(
        self,
        response: dict[str, Any],
        payload: dict[str, Any],
        *,
        trace_id: str,
        bridge_result: dict[str, Any] | None,
        trace_fields: dict[str, Any],
    ) -> dict[str, Any]:
        cloud_forge_bundle = schedule_rail_for_ugr(
            payload,
            trace_id=trace_id,
            bridge_result=bridge_result,
            tenant_manifold=resolve_tenant_manifold_for_forge(payload),
        )
        finalized = attach_cloud_forge_metadata(response, cloud_forge_bundle)
        finalized = attach_model_pool_to_response(finalized, payload)
        self._append_ugr_trace(trace_fields, cloud_forge_bundle)
        from src.aais_ul_substrate import wrap_ugr_response

        return wrap_ugr_response(finalized)

    def handle_request(self, request: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(request or {})
        question = str(payload.get("question") or "").strip()
        intent = str(payload.get("intent") or "general_qa").strip().lower()
        tenant_id = str(payload.get("tenant_id") or "default").strip() or "default"
        context = dict(payload.get("context") or {})
        lane_types = list(payload.get("lane_types") or [])
        trace_id = self._build_trace_id(payload)

        bridge_result = self.bridge.route_to_bridge(
            {
                "source": "ugr_runtime",
                "type": "deliberation_request",
                "payload": {
                    "question": question[:500],
                    "intent": intent,
                    "execution_intent": "observe",
                    "runtime_context": "live_runtime",
                    "trace_id": trace_id,
                    "bridge_attestation": build_bridge_attestation(
                        ingress="ugr_runtime",
                        surface="ugr_deliberate",
                        source_id=trace_id,
                        route="api.ugr.deliberate",
                        intent="observe",
                        runtime_context="live_runtime",
                        packet_type="deliberation_request",
                        runtime_dir=self.runtime_dir.parent,
                    ),
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        if bridge_result.get("decision") == DECISION_BLOCK:
            blocked = {
                "runtime_id": UGR_RUNTIME_ID,
                "runtime_version": UGR_RUNTIME_VERSION,
                "trace_id": trace_id,
                "status": "blocked",
                "summary": summarize_bridge_result(bridge_result),
                "bridge": bridge_result,
                "lane_results": [],
                "convergence": None,
            }
            return self._finalize_response(
                blocked,
                payload,
                trace_id=trace_id,
                bridge_result=bridge_result,
                trace_fields={
                    "trace_id": trace_id,
                    "status": "blocked",
                    "intent": intent,
                    "tenant_id": tenant_id,
                    "lane_count": 0,
                    "accepted_beliefs": 0,
                },
            )

        if not question:
            rejected = {
                "runtime_id": UGR_RUNTIME_ID,
                "runtime_version": UGR_RUNTIME_VERSION,
                "trace_id": trace_id,
                "status": "rejected",
                "summary": "UGR requires a non-empty question.",
                "bridge": bridge_result,
                "lane_results": [],
                "convergence": None,
            }
            return self._finalize_response(
                rejected,
                payload,
                trace_id=trace_id,
                bridge_result=bridge_result,
                trace_fields={
                    "trace_id": trace_id,
                    "status": "rejected",
                    "intent": intent,
                    "tenant_id": tenant_id,
                    "lane_count": 0,
                    "accepted_beliefs": 0,
                },
            )

        lane_specs = design_lane_set(intent, lane_types or None)
        shared_context = {
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "intent": intent,
            "question": question,
            "context": context,
            "bridge_result": bridge_result,
        }
        lane_results = run_lanes(trace_id, lane_specs, shared_context, ledger=self.ledger)
        convergence = self.convergence.converge(
            trace_id,
            lane_results,
            request=payload,
            policy_context={"tenant_id": tenant_id, "intent": intent},
        )

        accepted = [belief for belief in convergence.get("final_beliefs") or [] if belief.get("status") == "accepted"]
        if accepted:
            summary = (
                f"UGR accepted {len(accepted)} belief(s) from {len(lane_results)} lane(s) "
                f"for intent={intent}."
            )
        elif convergence.get("uncertainties"):
            summary = "UGR completed with contested beliefs; human review recommended."
        else:
            summary = "UGR completed but no beliefs met acceptance criteria."

        for belief in convergence.get("final_beliefs") or []:
            if belief.get("status") in {"accepted", "contested"}:
                self.ledger.append_claim(
                    {
                        "claim_id": self.ledger.make_claim_id(
                            str(belief.get("subject") or ""),
                            str(belief.get("predicate") or ""),
                            str(belief.get("object") or ""),
                            "convergence",
                        ),
                        "subject": belief.get("subject"),
                        "predicate": belief.get("predicate"),
                        "object": belief.get("object"),
                        "confidence": belief.get("confidence"),
                        "source_lane": "convergence",
                        "evidence_refs": list(belief.get("provenance") or []),
                        "tenant_scope": normalize_tenant_id(tenant_id),
                        "status": belief.get("status"),
                    }
                )

        response = {
            "runtime_id": UGR_RUNTIME_ID,
            "runtime_version": UGR_RUNTIME_VERSION,
            "trace_id": trace_id,
            "status": "ok",
            "summary": summary,
            "bridge": bridge_result,
            "lane_specs": [spec.to_dict() for spec in lane_specs],
            "lane_results": [lane.to_dict() for lane in lane_results],
            "convergence": convergence,
        }
        return self._finalize_response(
            response,
            payload,
            trace_id=trace_id,
            bridge_result=bridge_result,
            trace_fields={
                "trace_id": trace_id,
                "status": response["status"],
                "intent": intent,
                "tenant_id": tenant_id,
                "lane_count": len(lane_results),
                "accepted_beliefs": len(accepted),
            },
        )


def build_ugr_runtime():
    """Return monolith or distributed runtime based on UGR_DEPLOYMENT_MODE."""
    from src.ugr.cloud.mesh_config import deployment_mode

    if deployment_mode() == "distributed":
        from src.ugr.cloud.distributed_runtime import DistributedUnifiedGovernedRuntime

        return DistributedUnifiedGovernedRuntime()
    return UnifiedGovernedRuntime()


ugr_runtime = build_ugr_runtime()
