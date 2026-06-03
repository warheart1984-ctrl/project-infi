"""Register frontier HTTP providers on the AAIS provider registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.jarvis_provider_registry import ProviderConfig
from src.logger import get_logger
from src.providers.frontier_catalog import (
    FRONTIER_PROVIDER_SPECS,
    _resolve_api_key,
    build_http_adapter,
)
from src.providers.frontier_catalog import _azure_endpoint as resolve_azure_endpoint

if TYPE_CHECKING:
    from src.provider_registry import ProviderRegistry

logger = get_logger(__name__)


def register_frontier_providers(registry: ProviderRegistry) -> None:
    """Register all catalogued frontier providers (enabled only when configured)."""
    import os

    for spec in FRONTIER_PROVIDER_SPECS:
        api_key = _resolve_api_key(spec)
        model = os.getenv(spec.model_env, "").strip() or spec.default_model
        if spec.name == "azure_openai":
            endpoint = resolve_azure_endpoint()
            configured = bool(api_key and endpoint)
        else:
            endpoint = os.getenv(spec.base_url_env, "").strip() or spec.default_base_url
            configured = bool(api_key and endpoint)

        meta = {
            "kind": "remote",
            "summary": spec.summary,
            "frontier_family": spec.frontier_family,
            "model_catalog_note": spec.model_catalog_note,
            "model": model,
            "endpoint": endpoint or spec.default_base_url,
            "activation_hint": spec.activation_hint,
        }

        if not configured:
            meta["reason"] = f"{spec.api_key_env} is not set."
            registry.register(
                ProviderConfig(
                    name=spec.name,
                    display_name=spec.display_name,
                    enabled=False,
                    supports_stream=spec.supports_stream,
                    meta=meta,
                ),
                adapter=None,
            )
            continue

        try:
            adapter = build_http_adapter(spec)
            meta["reason"] = f"{spec.display_name} is configured."
            meta["activation_hint"] = ""
            meta["model"] = adapter.model
            registry.register(
                ProviderConfig(
                    name=spec.name,
                    display_name=spec.display_name,
                    enabled=True,
                    supports_stream=spec.supports_stream,
                    meta=meta,
                ),
                adapter=adapter,
            )
        except Exception as exc:  # pragma: no cover - optional runtime deps
            logger.warning("%s provider unavailable: %s", spec.name, exc)
            meta["reason"] = str(exc)
            registry.register(
                ProviderConfig(
                    name=spec.name,
                    display_name=spec.display_name,
                    enabled=False,
                    supports_stream=spec.supports_stream,
                    meta=meta,
                ),
                adapter=None,
            )
