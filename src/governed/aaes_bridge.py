"""Step 3 — Convert URG receipt into an AAES execution via DAR-Z bridge."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from src.aaes_os import AAESRequest, CognitiveOrchestrator
from src.aaes_os.modules.daniel import ModuleRegistry
from src.aaes_os.trace_store import TraceStore

from src.governed.config import GovernedRuntimeConfig, get_governed_config
from src.governed.darz_bridge import build_darz_receipt_from_urg


def _normalize_aaes_receipt(result: dict[str, Any]) -> dict[str, Any]:
    status = str(result.get("status") or "")
    normalized = dict(result)
    if status == "ok":
        normalized["status"] = "executed"
    normalized["executed"] = status in {"ok", "executed", "warn"}
    return normalized


def _post_aaes(payload: dict[str, Any], config: GovernedRuntimeConfig) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        config.aaes_url(),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_to_aaes(
    *,
    law_eval: dict[str, Any],
    urg_receipt: dict[str, Any],
    steward_identity: dict[str, Any],
    user_text: str = "",
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Convert URG mission receipt → AAES execution receipt."""
    cfg = config or get_governed_config()
    darz_bundle = build_darz_receipt_from_urg(
        law_eval=law_eval,
        urg_receipt=urg_receipt,
        steward_identity=steward_identity,
        config=cfg,
    )
    darz_receipt = darz_bundle["receipt"]
    darz_summary = darz_bundle["summary"]
    mission_id = str(urg_receipt.get("mission_id") or "")
    law_eval_id = str(law_eval.get("id") or "")

    execute_body = {
        "prompt": str(law_eval.get("nova_text") or user_text or "Governed mission execution"),
        "actor_id": "aais.governed_mission",
        "session_id": str(steward_identity.get("session_id") or ""),
        "trace_id": f"aaes-governed-{mission_id or law_eval_id}",
        "metadata": {
            "intent": "governed_constitutional_spine",
            "module_id": cfg.aaes_execution_module_id,
            "operation": "execute",
            "args": {
                "mission_id": mission_id,
                "law_eval_id": law_eval_id,
                "ugr_status": urg_receipt.get("status"),
                "darz": darz_summary,
                "darz_bridge_hash": darz_receipt.get("bridge_hash"),
                "steward_id": steward_identity.get("steward_id") or steward_identity.get("operator_id"),
                "identity": steward_identity,
            },
        },
    }

    if cfg.use_http_aaes:
        try:
            result = _post_aaes(execute_body, cfg)
        except error.URLError as exc:
            raise RuntimeError(f"AAES execute HTTP failed: {exc}") from exc
    else:
        orchestrator = cfg.orchestrator or CognitiveOrchestrator(
            trace_store=TraceStore(),
            module_registry=ModuleRegistry(include_daniel=True),
        )
        aaes_result = orchestrator.execute(
            AAESRequest(
                prompt=execute_body["prompt"],
                actor_id=execute_body["actor_id"],
                session_id=execute_body.get("session_id"),
                trace_id=execute_body.get("trace_id"),
                metadata=dict(execute_body.get("metadata") or {}),
            )
        )
        result = {
            "trace_id": aaes_result.trace_id,
            "span_id": aaes_result.span_id,
            "status": aaes_result.status,
            "blocked": aaes_result.blocked,
            "outcome": aaes_result.outcome,
            "explanation": aaes_result.explanation,
        }

    receipt = _normalize_aaes_receipt(result)
    receipt["mission_id"] = mission_id
    receipt["law_eval_id"] = law_eval_id
    receipt["darz_bridge_hash"] = darz_receipt.get("bridge_hash")
    receipt["darz"] = darz_summary
    receipt["steward_id"] = str(
        steward_identity.get("steward_id") or steward_identity.get("operator_id") or ""
    )
    receipt["execution_id"] = str(receipt.get("trace_id") or execute_body.get("trace_id") or "")
    return receipt
