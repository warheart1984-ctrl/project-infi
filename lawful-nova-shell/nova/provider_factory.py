"""Optional frontier model backend for Lawful Nova (OpenAI, NVIDIA NIM, etc.)."""

from __future__ import annotations

import os
from typing import Any

LAWFUL_NOVA_MODEL_ALIASES = frozenset({"lawful-nova", "lawfulnova"})


def resolve_provider_model(requested: str | None, provider: Any | None = None) -> str | None:
    """Map Cursor-facing model ids (lawful-nova) to the frontier provider's real model id."""
    if provider is None:
        return requested
    provider_default = getattr(provider, "model", None)
    if not requested:
        return provider_default
    normalized = requested.strip().lower().replace("_", "-")
    alias = normalized.replace("-", "")
    if normalized in LAWFUL_NOVA_MODEL_ALIASES or alias == "lawfulnova":
        return provider_default
    return requested


def resolve_frontier_provider() -> Any | None:
    """Return an HttpChatProvider when NOVA_FRONTIER_PROVIDER is set and configured."""
    raw = os.environ.get("NOVA_FRONTIER_PROVIDER", "").strip()
    if not raw:
        return None

    try:
        from src.providers.frontier_catalog import (
            FRONTIER_PROVIDER_SPECS,
            _azure_endpoint,
            _resolve_api_key,
            build_http_adapter,
            resolve_provider_alias,
        )
    except ImportError:
        return None

    provider_name = resolve_provider_alias(raw)
    spec_by_name = {spec.name: spec for spec in FRONTIER_PROVIDER_SPECS}
    spec = spec_by_name.get(provider_name)
    if spec is None:
        return None

    api_key = _resolve_api_key(spec)
    if spec.name == "azure_openai":
        configured = bool(api_key and _azure_endpoint())
    else:
        endpoint = os.getenv(spec.base_url_env, "").strip() or spec.default_base_url
        configured = bool(api_key and endpoint)
    if not configured:
        return None

    return build_http_adapter(spec)


def frontier_provider_status() -> dict[str, Any]:
    """Summarize frontier provider env for /health and startup logs."""
    raw = os.environ.get("NOVA_FRONTIER_PROVIDER", "").strip()
    if not raw:
        return {"frontier_provider": None, "frontier_configured": False}

    provider = resolve_frontier_provider()
    if provider is None:
        return {
            "frontier_provider": raw,
            "frontier_configured": False,
            "frontier_reason": "NOVA_FRONTIER_PROVIDER set but provider is not configured (missing API key or endpoint).",
        }

    return {
        "frontier_provider": getattr(provider, "provider_id", raw),
        "frontier_model": getattr(provider, "model", None),
        "frontier_configured": True,
    }
