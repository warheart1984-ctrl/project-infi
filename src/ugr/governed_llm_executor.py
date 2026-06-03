"""Governed LLM execution commit layer — honors PROPOSED envelopes after bridge clearance."""

# Mythic: Governed Llm Executor
# Engineering: GovernedLlmExecutorEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import asyncio
import os
from typing import Any

from src.aais_governed_llm_module import GOVERNED_LLM_MODULE_ID, validate_governed_llm_envelope
from src.jarvis_protocol import JarvisMessage
from src.provider_registry import ProviderRegistry, provider_registry


UGR_LLM_EXECUTE_ENV = "UGR_LLM_EXECUTE"
UGR_LLM_EXECUTOR_VERSION = "1.0"
UGR_LLM_TEMPERATURE = 0.0


def apply_ugr_temperature_cap(provider_request: dict[str, Any] | None) -> dict[str, Any]:
    capped = dict(provider_request or {})
    overrides = dict(capped.get("generation_overrides") or {})
    overrides.update({"temperature": UGR_LLM_TEMPERATURE, "temperature_max": UGR_LLM_TEMPERATURE})
    capped["generation_overrides"] = overrides
    return capped


def llm_execution_enabled() -> bool:
    raw = os.getenv(UGR_LLM_EXECUTE_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _bridge_allows_execution(bridge_result: dict[str, Any]) -> bool:
    decision = str(bridge_result.get("decision") or "BLOCK").upper()
    return decision in {"ALLOW", "DEGRADE"} and bool(bridge_result.get("execution_allowed", True))


def build_messages_for_proposal(*, question: str, envelope: dict[str, Any]) -> list[dict[str, Any]]:
    route = dict(envelope.get("provider_request") or {})
    instruction = str(route.get("instruction") or "").strip()
    system_parts = [
        "You are a governed AAIS deliberation assistant.",
        "Respond with concise, evidence-oriented analysis only.",
        instruction,
    ]
    user_question = str(question or "").strip()
    if not user_question:
        user_question = "Provide a bounded analysis for the governed trace."
    return [
        {"role": "system", "content": " ".join(part for part in system_parts if part)},
        {"role": "user", "content": user_question[:4000]},
    ]


def execute_governed_llm_proposal(
    envelope: dict[str, Any],
    *,
    bridge_result: dict[str, Any],
    question: str,
    provider_registry_instance: ProviderRegistry | None = None,
    force_execute: bool = False,
) -> dict[str, Any]:
    """Execute a bounded provider proposal when execution is explicitly enabled."""
    if not validate_governed_llm_envelope(envelope):
        return _wrap_ul_payload({
            "status": "BLOCKED",
            "reason": "invalid_governed_envelope",
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    if envelope.get("status") != "PROPOSED":
        return _wrap_ul_payload({
            "status": "SKIPPED",
            "reason": "envelope_not_proposed",
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    if not _bridge_allows_execution(bridge_result):
        return _wrap_ul_payload({
            "status": "BLOCKED",
            "reason": "bridge_decision_blocked",
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    if not llm_execution_enabled() and not force_execute:
        return _wrap_ul_payload({
            "status": "SKIPPED",
            "reason": "execution_disabled",
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    capped_request = apply_ugr_temperature_cap(dict(envelope.get("provider_request") or {}))
    provider_id = str(capped_request.get("provider") or "local").strip().lower()
    registry = provider_registry_instance or provider_registry
    adapter = registry.get(provider_id)
    if adapter is None or not registry.can_invoke(provider_id):
        return _wrap_ul_payload({
            "status": "BLOCKED",
            "reason": "provider_unavailable",
            "provider": provider_id,
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    messages = build_messages_for_proposal(question=question, envelope=envelope)
    overrides = dict(capped_request.get("generation_overrides") or {})
    temperature = float(overrides.get("temperature", UGR_LLM_TEMPERATURE))
    max_tokens = int(overrides.get("max_tokens") or 512)
    response_mode = str(capped_request.get("response_mode") or "think")

    try:
        response = asyncio.run(
            adapter.invoke(
                [JarvisMessage.from_dict(item) for item in messages],
                max_tokens=max_tokens,
                temperature=temperature,
                response_mode=response_mode,
                mode=response_mode,
                model=capped_request.get("provider_model"),
                routing_profile={
                    "provider": provider_id,
                    "provider_label": capped_request.get("provider_label"),
                    "provider_kind": capped_request.get("provider_kind"),
                    "provider_model": capped_request.get("provider_model"),
                    "execution_backend": capped_request.get("execution_backend"),
                    "route_id": capped_request.get("route_id"),
                },
            )
        )
    except Exception as exc:
        return _wrap_ul_payload({
            "status": "ERROR",
            "reason": "provider_invoke_failed",
            "error": str(exc),
            "provider": provider_id,
            "executor_version": UGR_LLM_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    content = str(getattr(response, "content", "") or "").strip()
    input_tokens = getattr(response, "input_tokens", None)
    output_tokens = getattr(response, "output_tokens", None)
    tokens_used = int(output_tokens or 0) + int(input_tokens or 0)

    return _wrap_ul_payload({
        "status": "EXECUTED",
        "reason": "governed_provider_execution_complete",
        "executor_version": UGR_LLM_EXECUTOR_VERSION,
        "module_id": GOVERNED_LLM_MODULE_ID,
        "provider": provider_id,
        "provider_model": getattr(response, "model", None) or capped_request.get("provider_model"),
        "content": content[:8000],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens_used": tokens_used,
        "proposal_only": False,
        "execution_authority": "governed_commit",
        "provider_request": capped_request,
    })
