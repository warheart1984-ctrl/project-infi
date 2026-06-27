from __future__ import annotations

from typing import Any

from .provider_base import NovaProvider
from .provider_external import ExternalProvider
from .provider_local import LocalDeterministicProvider
from .provider_ollama import OllamaProvider


def build_provider(config: dict[str, Any]) -> NovaProvider:
    provider_name = str(config.get("provider") or "local").lower()
    timeout = float(config.get("timeout") or 60)
    if provider_name == "ollama":
        return OllamaProvider(
            base_url=str(config.get("ollama_url") or "http://127.0.0.1:11434"),
            model=str(config.get("ollama_model") or "qwen2.5-coder:7b"),
            timeout=timeout,
        )
    if provider_name == "external":
        return ExternalProvider(
            base_url=str(config.get("external_url") or ""),
            api_key=config.get("external_api_key"),
            model=str(config.get("external_model") or "external-model"),
            timeout=timeout,
        )
    return LocalDeterministicProvider(model=str(config.get("local_model") or "nova-local"))
