"""Step 1 — Lawful Nova LAW_EVAL via identity, law ledger, reference, and panel bridges."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from urllib import error, request
from uuid import uuid4

from nova.bridges import identity_bridge, law_ledger_bridge, panel_store, reference_bridge
from nova.bridges.nova_to_urg_bridge import build_law_context
from nova.law_kernel.types import LawEvent
from nova.runtime_factory import build_lawful_llm

from src.governed.config import GovernedRuntimeConfig, get_governed_config


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _law_eval_id(evaluation: dict[str, Any]) -> str:
    proof = str(evaluation.get("invariant_proof_id") or "").strip()
    if proof:
        return proof
    candidate = dict(evaluation.get("candidate_intent") or {})
    return str(candidate.get("id") or f"law-eval-{uuid4().hex[:12]}")


def _extract_evaluation(nova_response: dict[str, Any]) -> dict[str, Any]:
    law_kernel = dict(nova_response.get("law_kernel") or {})
    evaluation = dict(law_kernel.get("evaluation") or {})
    if evaluation:
        return evaluation
    return law_kernel


def _normalize_law_eval(
    *,
    nova_response: dict[str, Any],
    evaluation: dict[str, Any],
    law_context: dict[str, Any],
    t5_refs: dict[str, Any],
) -> dict[str, Any]:
    law_eval_id = _law_eval_id(evaluation)
    candidate = dict(evaluation.get("candidate_intent") or {})
    payload = dict(candidate.get("payload") or {})
    admitted = str(nova_response.get("decision") or "").upper() in {"EXECUTED", "ADMIT"}
    if not admitted:
        admitted = str(evaluation.get("decision") or "").lower() in {"admit", "transform"}
    return {
        "status": "ok" if admitted else "denied",
        "id": law_eval_id,
        "intent": str(payload.get("intent") or payload.get("intent_type") or "governed_constitutional_spine"),
        "intent_type": "mission",
        "evaluation": evaluation,
        "law_context": law_context,
        "t5_refs": t5_refs,
        "panels": {
            "reflexive": panel_store.get_panel_store().list_reflexive_events(),
            "steward": panel_store.get_panel_store().list_steward_events(),
            "perception": panel_store.get_panel_store().list_perception_snapshots(),
        },
        "nova_text": nova_response.get("text"),
        "receipt": nova_response.get("receipt"),
        "receipt_verified": nova_response.get("receipt_verified"),
        "law_hash": _digest(json.dumps(evaluation, sort_keys=True, default=str)),
    }


def _call_nova_http(*, text: str, config: GovernedRuntimeConfig, law_context: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(
        {
            "prompt": text,
            "tenant_id": config.tenant_id,
            "capability": config.capability,
            "governed": True,
            "intent_type": "mission",
            "law_context": law_context,
        }
    ).encode("utf-8")
    req = request.Request(
        config.nova_chat_url(),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_nova_in_process(*, text: str, config: GovernedRuntimeConfig) -> dict[str, Any]:
    llm = build_lawful_llm(operator_session_id="governed-mission", signing_secret="governed-mission-secret")
    turn = llm.ask(text, tenant_id=config.tenant_id, capability=config.capability)
    return {
        "text": turn.text,
        "decision": turn.voss_runtime.get("decision"),
        "law_kernel": turn.law_kernel,
        "receipt": turn.receipt,
        "receipt_verified": llm.verify_receipt(turn.receipt),
    }


def call_lawful_nova(
    *,
    text: str,
    steward_identity: dict[str, Any],
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Call Lawful Nova and return a normalized LAW_EVAL artifact."""
    cfg = config or get_governed_config()
    law_context = build_law_context()
    law_context["steward_identity"] = dict(steward_identity)
    law_context["steward_id"] = str(
        steward_identity.get("steward_id")
        or steward_identity.get("operator_id")
        or law_context.get("steward_id")
        or "operator"
    )

    t5_binding = reference_bridge.current_reference_binding()
    t5_refs = {
        "ref_hash": t5_binding.ref_hash,
        "bound": t5_binding.bound,
        "metrics": dict(t5_binding.metrics),
    }

    try:
        if cfg.use_http_nova:
            nova_response = _call_nova_http(text=text, config=cfg, law_context=law_context)
        else:
            raise error.URLError("in-process")
    except error.URLError:
        nova_response = _call_nova_in_process(text=text, config=cfg)

    evaluation = _extract_evaluation(nova_response)
    law_eval = _normalize_law_eval(
        nova_response=nova_response,
        evaluation=evaluation,
        law_context=law_context,
        t5_refs=t5_refs,
    )

    law_ledger_bridge.record_law_event(
        LawEvent(
            entry_type="LAW_EVAL",
            law_id="governed-mission",
            law_hash=law_eval["law_hash"],
            epoch=0,
            payload={
                "law_eval_id": law_eval["id"],
                "intent": law_eval["intent"],
                "evaluation": evaluation,
                "introduced_by": "nova",
                "steward_id": law_context["steward_id"],
            },
            signed_by="nova",
        )
    )

    identity = identity_bridge.get_current_identity()
    panel_store.get_panel_store().append_perception_snapshot(
        {
            "intent_id": law_eval["id"],
            "epoch_id": identity.epoch,
            "inputs": {"text": text, "steward": steward_identity},
            "outputs": {"law_eval_id": law_eval["id"], "intent": law_eval["intent"]},
            "confidence": 1.0 if law_eval["status"] == "ok" else 0.0,
            "anomaly_score": 0.0,
        }
    )
    panel_store.get_panel_store().append_steward_event(
        kind="law_eval",
        payload={
            "law_eval_id": law_eval["id"],
            "status": law_eval["status"],
            "steward_id": law_context["steward_id"],
        },
    )

    return law_eval
