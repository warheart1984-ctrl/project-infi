"""Turn-level model routing for Jarvis.

Jarvis can feel smarter without loading many heavyweight backends by routing
each turn through a stronger local generation profile. This module decides
which local "brain profile" should drive the answer, then exposes a compact
trace the UI can show.
"""

# Mythic: Model Routing
# Engineering: ModelRoutingEngine
from __future__ import annotations

import os


from src.providers.frontier_catalog import (
    frontier_default_models,
    frontier_model_envs,
    frontier_remote_labels,
)

REMOTE_PROVIDER_LABELS = {
    "claude": "Claude — First Sister",
    "openrouter": "OpenRouter — Free Relay",
    **frontier_remote_labels(),
}

REMOTE_PROVIDER_MODEL_ENVS = {
    "claude": "AAIS_CLAUDE_MODEL",
    "openrouter": "AAIS_OPENROUTER_MODEL",
    **frontier_model_envs(),
}

REMOTE_PROVIDER_DEFAULT_MODELS = {
    "claude": "claude-3-7-sonnet-20250219",
    "openrouter": "openrouter/free",
    **frontier_default_models(),
}


MODEL_ROUTES = {
    "tiny_companion": {
        "label": "Tiny Companion",
        "summary": "Keep the answer brief, warm, and narrowly focused on one useful thought.",
        "adapter_mode": "fast",
        "generation_overrides": {
            "temperature_max": 0.32,
            "min_new_tokens_floor": 12,
            "min_new_tokens_ratio": 0.14,
            "repetition_penalty": 1.04,
            "input_max_length": 1280,
            "no_repeat_ngram_size": 3,
        },
    },
    "small_companion": {
        "label": "Small Companion",
        "summary": "Keep the answer calm, grounded, and companion-led with one or two useful thoughts.",
        "adapter_mode": "fast",
        "generation_overrides": {
            "temperature_max": 0.28,
            "min_new_tokens_floor": 18,
            "min_new_tokens_ratio": 0.18,
            "repetition_penalty": 1.05,
            "input_max_length": 1536,
            "no_repeat_ngram_size": 3,
        },
    },
    "super_companion": {
        "label": "Super Companion",
        "summary": "Keep the answer deeply grounded, organized across threads, and companion-led without taking authority.",
        "adapter_mode": "think",
        "generation_overrides": {
            "temperature_max": 0.24,
            "min_new_tokens_floor": 26,
            "min_new_tokens_ratio": 0.22,
            "repetition_penalty": 1.07,
            "input_max_length": 1792,
            "no_repeat_ngram_size": 4,
        },
    },
    "rapid_local": {
        "label": "Rapid Local",
        "summary": "Keep latency low and answer directly with minimal drift.",
        "adapter_mode": "fast",
        "generation_overrides": {
            "temperature_max": 0.24,
            "min_new_tokens_floor": 10,
            "min_new_tokens_ratio": 0.12,
            "repetition_penalty": 1.06,
            "input_max_length": 1440,
            "no_repeat_ngram_size": 3,
        },
    },
    "deliberate_local": {
        "label": "Deliberate Local",
        "summary": "Take a slower local reasoning pass and keep the answer grounded.",
        "adapter_mode": "think",
        "generation_overrides": {
            "temperature_max": 0.2,
            "min_new_tokens_floor": 28,
            "min_new_tokens_ratio": 0.24,
            "repetition_penalty": 1.08,
            "input_max_length": 2048,
            "no_repeat_ngram_size": 3,
        },
    },
    "code_analyst": {
        "label": "Code Analyst",
        "summary": "Bias toward file evidence, implementation tradeoffs, and concrete edits.",
        "adapter_mode": "think",
        "generation_overrides": {
            "temperature_max": 0.16,
            "min_new_tokens_floor": 32,
            "min_new_tokens_ratio": 0.24,
            "repetition_penalty": 1.11,
            "input_max_length": 2176,
            "no_repeat_ngram_size": 4,
        },
    },
    "bug_hunter": {
        "label": "Bug Hunter",
        "summary": "Bias toward failure signals, root cause, and the fastest proof step.",
        "adapter_mode": "debug",
        "generation_overrides": {
            "temperature_max": 0.12,
            "min_new_tokens_floor": 32,
            "min_new_tokens_ratio": 0.26,
            "repetition_penalty": 1.13,
            "input_max_length": 2176,
            "no_repeat_ngram_size": 4,
        },
    },
    "shipwright": {
        "label": "Shipwright",
        "summary": "Bias toward the smallest working slice and an implementation order.",
        "adapter_mode": "builder",
        "generation_overrides": {
            "temperature_max": 0.22,
            "min_new_tokens_floor": 24,
            "min_new_tokens_ratio": 0.2,
            "repetition_penalty": 1.08,
            "input_max_length": 1920,
            "no_repeat_ngram_size": 3,
        },
    },
    "evidence_synthesizer": {
        "label": "Evidence Synthesizer",
        "summary": "Bias toward current evidence, comparisons, and tighter sourced conclusions.",
        "adapter_mode": "research",
        "generation_overrides": {
            "temperature_max": 0.14,
            "min_new_tokens_floor": 28,
            "min_new_tokens_ratio": 0.23,
            "repetition_penalty": 1.09,
            "input_max_length": 2304,
            "no_repeat_ngram_size": 4,
        },
    },
    "operator_guardian": {
        "label": "Operator Guardian",
        "summary": "Bias toward local state, approvals, and safe next actions.",
        "adapter_mode": "operator",
        "generation_overrides": {
            "temperature_max": 0.14,
            "min_new_tokens_floor": 18,
            "min_new_tokens_ratio": 0.18,
            "repetition_penalty": 1.08,
            "input_max_length": 1792,
            "no_repeat_ngram_size": 3,
        },
    },
    "training_coach": {
        "label": "Training Coach",
        "summary": "Bias toward realistic local-model training, evals, and serving tradeoffs.",
        "adapter_mode": "builder",
        "generation_overrides": {
            "temperature_max": 0.18,
            "min_new_tokens_floor": 28,
            "min_new_tokens_ratio": 0.22,
            "repetition_penalty": 1.1,
            "input_max_length": 2176,
            "no_repeat_ngram_size": 4,
        },
    },
    "story_room": {
        "label": "Story Room",
        "summary": "Bias toward voice, continuity, and cleaner creative output without losing structure.",
        "adapter_mode": "think",
        "generation_overrides": {
            "temperature_max": 0.34,
            "min_new_tokens_floor": 24,
            "min_new_tokens_ratio": 0.2,
            "repetition_penalty": 1.05,
            "input_max_length": 1920,
            "no_repeat_ngram_size": 3,
        },
    },
}


def _build_surface_authority_profile(response_mode: str, route_id: str) -> dict:
    """Expose the surface-vs-authority split for one routed turn."""
    normalized_mode = _normalize_mode(response_mode)
    if normalized_mode == "tiny" or route_id == "tiny_companion":
        surface_identity = "tiny_nova"
    elif normalized_mode == "small" or route_id == "small_companion":
        surface_identity = "small_nova"
    elif normalized_mode in {"super", "governed_full"} or route_id == "super_companion":
        surface_identity = "super_nova"
    else:
        surface_identity = "jarvis"
    return {
        "authority_lane": "jarvis",
        "routing_authority": "jarvis",
        "surface_identity": surface_identity,
        "surface_priority": "delegated_surface" if surface_identity != "jarvis" else "authority_surface",
        "surface_replaces_authority": False,
        "authority_model": "layered_role_specialized",
        "system_shape": "organismic",
    }


def _normalize_mode(value: str | None) -> str:
    cleaned = " ".join(str(value or "").lower().split()).strip().replace("-", "_")
    return cleaned or "fast"


def _normalize_provider(value: str | None) -> str:
    cleaned = " ".join(str(value or "").lower().split()).strip().replace("-", "_")
    if cleaned in {"automatic", "best", "best_provider", "best_available", "auto_best"}:
        cleaned = "auto"
    return cleaned or "local"


def resolve_model_route(
    *,
    response_mode: str,
    specialist_profile: dict | None = None,
    specialist_preset: dict | None = None,
    god_brain: dict | None = None,
    workspace_hits: int = 0,
    research_sources: int = 0,
    policy_status: dict | None = None,
    tool_type: str | None = None,
    preferred_provider: str | None = None,
    provider_available=None,
) -> dict:
    """Resolve the best local model route for a turn."""
    normalized_mode = _normalize_mode(response_mode)
    domain = (specialist_profile or {}).get("domain")
    focus = (specialist_profile or {}).get("focus")
    preset_id = (specialist_preset or {}).get("id")
    action_bias = (god_brain or {}).get("action_bias")
    posture = (policy_status or {}).get("posture", "nominal")

    route_id = "rapid_local"
    reason = "fast_default"

    if tool_type:
        route_id = "operator_guardian"
        reason = "tool_path"
    elif normalized_mode == "tiny":
        route_id = "tiny_companion"
        reason = "tiny_persona"
    elif normalized_mode == "small":
        route_id = "small_companion"
        reason = "small_persona"
    elif normalized_mode in {"super", "governed_full"}:
        route_id = "super_companion"
        reason = "super_persona"
    elif domain == "training":
        route_id = "training_coach"
        reason = "training_domain"
    elif domain == "writing":
        route_id = "story_room"
        reason = "writing_domain"
    elif normalized_mode == "research" or research_sources > 0:
        route_id = "evidence_synthesizer"
        reason = "research_evidence"
    elif normalized_mode == "operator" or posture in {"cautious", "degraded"}:
        route_id = "operator_guardian"
        reason = "operator_safety"
    elif focus in {"debugging", "testing", "review"} or normalized_mode == "debug":
        route_id = "bug_hunter"
        reason = "debug_focus"
    elif focus in {"architecture", "refactor", "integration"}:
        route_id = "code_analyst"
        reason = "coding_analysis"
    elif normalized_mode == "builder" or focus in {"implementation", "finetuning", "dataset"}:
        route_id = "shipwright" if domain != "training" else "training_coach"
        reason = "builder_route"
    elif normalized_mode == "think" and workspace_hits > 0:
        route_id = "code_analyst" if domain == "coding" else "deliberate_local"
        reason = "think_with_workspace"
    elif normalized_mode == "think":
        route_id = "deliberate_local"
        reason = "think_default"

    route = dict(MODEL_ROUTES[route_id])
    route["id"] = route_id
    route["reason"] = reason
    route["response_mode"] = normalized_mode
    route["domain"] = domain
    route["focus"] = focus
    route["preset_id"] = preset_id
    route["workspace_hits"] = workspace_hits
    route["research_sources"] = research_sources
    route["policy_posture"] = posture
    route["action_bias"] = action_bias
    route["summary"] = route["summary"]
    route.update(_build_surface_authority_profile(normalized_mode, route_id))
    selected_provider = "local"
    provider_reason = "local_primary"
    normalized_provider = _normalize_provider(preferred_provider)
    auto_remote_allowed = os.getenv("AAIS_ENABLE_CLAUDE_AUTO_ROUTING", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    auto_openrouter_allowed = os.getenv("AAIS_ENABLE_OPENROUTER_AUTO_ROUTING", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    provider_check = provider_available or (lambda provider_id: False)

    auto_best_requested = normalized_provider == "auto"
    remote_eligible = (
        not tool_type
        and normalized_mode in {"think", "research"}
        and route_id not in {"operator_guardian", "bug_hunter", "code_analyst", "shipwright", "training_coach"}
    )

    if normalized_provider not in {"", "local", "auto"} and provider_check(normalized_provider):
        selected_provider = normalized_provider
        provider_reason = "manual_preference"
    elif auto_best_requested:
        if provider_check("claude") and remote_eligible:
            selected_provider = "claude"
            provider_reason = "auto_best_research" if normalized_mode == "research" else "auto_best_reasoning"
        elif provider_check("openrouter") and remote_eligible:
            selected_provider = "openrouter"
            provider_reason = "auto_best_openrouter"
        else:
            selected_provider = "local"
            provider_reason = "auto_best_local"
    elif (
        auto_remote_allowed
        and normalized_provider in {"", "local"}
        and provider_check("claude")
        and remote_eligible
    ):
        selected_provider = "claude"
        provider_reason = (
            "auto_research_escalation"
            if normalized_mode == "research" or research_sources >= 1
            else "auto_claude_hotwire"
        )
    elif (
        auto_openrouter_allowed
        and normalized_provider in {"", "local"}
        and provider_check("openrouter")
        and normalized_mode in {"think", "research"}
    ):
        selected_provider = "openrouter"
        provider_reason = "auto_free_escalation"

    route["provider"] = selected_provider
    route["provider_label"] = REMOTE_PROVIDER_LABELS.get(selected_provider, "Local Heroine")
    route["provider_kind"] = "remote" if selected_provider != "local" else "local"
    route["provider_reason"] = provider_reason
    route["provider_model"] = (
        os.getenv(REMOTE_PROVIDER_MODEL_ENVS[selected_provider], "").strip()
        or REMOTE_PROVIDER_DEFAULT_MODELS.get(selected_provider)
        if selected_provider in REMOTE_PROVIDER_MODEL_ENVS
        else None
    )
    route["execution_backend"] = "remote_provider" if selected_provider != "local" else "local_model"
    route["instruction"] = (
        f"Model route: {route['label']}. {route['summary']} "
        "Use this routing silently and return one grounded answer."
    )
    return route
