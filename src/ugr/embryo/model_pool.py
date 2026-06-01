"""Governed model pool v0 — tier × rail × tenant × law routing (proposal-only)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.platform.tenant_registry import normalize_tenant_id


UGR_MODEL_POOL_VERSION = "0.1"
CLAIM_ASSERTED = "asserted"


def _default_pool_path() -> Path:
    env_path = os.getenv("UGR_MODEL_POOL_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "model-pool.json"


def extract_governed_llm_from_lanes(lane_results: list[Any]) -> dict[str, Any] | None:
    for lane in lane_results or []:
        payload = lane.to_dict() if hasattr(lane, "to_dict") else dict(lane or {})
        if payload.get("lane_type") != "llm":
            continue
        envelope = dict((payload.get("payload") or {}).get("governed_llm") or {})
        if envelope:
            return envelope
    return None


class ModelPoolRouter:
    """Resolve a governed model pool slot from rail plan and LLM lane output."""

    def __init__(self, config_path: str | Path | None = None):
        self.path = Path(config_path) if config_path else _default_pool_path()
        self._config = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    def list_slots(self) -> list[dict[str, Any]]:
        slots = dict(self._config.get("slots") or {})
        return [{"tier": tier, **dict(spec)} for tier, spec in slots.items()]

    def _allowed_tiers(self, rail: str) -> list[str]:
        caps = dict(self._config.get("rail_caps") or {})
        allowed = list(caps.get(str(rail or "NORMAL").upper()) or caps.get("NORMAL") or ["mid"])
        return [str(item).strip().lower() for item in allowed if str(item).strip()]

    def resolve(
        self,
        *,
        request: dict[str, Any],
        trace_id: str,
        cloud_forge: dict[str, Any] | None = None,
        lane_results: list[Any] | None = None,
        bridge_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bundle = dict(cloud_forge or {})
        decision = dict(bundle.get("rail_decision") or {})
        plan = dict(bundle.get("cognition_plan") or {})
        rail = str(decision.get("rail") or "NORMAL").upper()
        requested_tier = str(plan.get("model_tier") or self._config.get("default_tier") or "mid").lower()
        allowed = self._allowed_tiers(rail)
        tier = requested_tier if requested_tier in allowed else (allowed[0] if allowed else "mid")
        slot_spec = dict((self._config.get("slots") or {}).get(tier) or {})
        governed_llm = extract_governed_llm_from_lanes(list(lane_results or []))
        provider_request = dict((governed_llm or {}).get("provider_request") or {})
        overrides = dict(self._config.get("generation_overrides") or {})
        overrides.update(dict(provider_request.get("generation_overrides") or {}))

        tenant_scope = normalize_tenant_id(request.get("tenant_id"))
        law_required_proof = bool(dict(request.get("context") or {}).get("required_proof"))
        if law_required_proof or rail == "SAFE":
            tier = allowed[0] if allowed else "tiny"
            slot_spec = dict((self._config.get("slots") or {}).get(tier) or slot_spec)

        return {
            "pool_version": str(self._config.get("pool_version") or UGR_MODEL_POOL_VERSION),
            "trace_id": trace_id,
            "tenant_scope": tenant_scope,
            "rail": rail,
            "requested_tier": requested_tier,
            "selected_tier": tier,
            "slot_id": str(slot_spec.get("slot_id") or f"pool-{tier}-default"),
            "provider": str(provider_request.get("provider") or slot_spec.get("provider") or "local"),
            "provider_label": str(
                provider_request.get("provider_label") or slot_spec.get("provider_label") or "Local"
            ),
            "execution_backend": str(
                provider_request.get("execution_backend") or slot_spec.get("execution_backend") or "local"
            ),
            "response_mode": str(provider_request.get("response_mode") or slot_spec.get("response_mode") or "think"),
            "proposal_only": True,
            "execution_authority": "none",
            "generation_overrides": overrides,
            "governed_llm_status": str((governed_llm or {}).get("status") or "not_invoked"),
            "governed_llm_reason": str((governed_llm or {}).get("reason") or ""),
            "bridge_decision": str((bridge_result or {}).get("decision") or "UNKNOWN"),
            "claim_status": CLAIM_ASSERTED,
        }


def attach_model_pool_to_response(
    response: dict[str, Any],
    request: dict[str, Any],
    *,
    router: ModelPoolRouter | None = None,
) -> dict[str, Any]:
    pool = router or ModelPoolRouter()
    trace_id = str(response.get("trace_id") or "")
    slot = pool.resolve(
        request=request,
        trace_id=trace_id,
        cloud_forge=dict(response.get("cloud_forge") or {}),
        lane_results=list(response.get("lane_results") or []),
        bridge_result=dict(response.get("bridge") or {}),
    )
    updated = dict(response)
    updated["model_pool"] = slot
    return updated
