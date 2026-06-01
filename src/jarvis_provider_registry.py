"""Generic Jarvis provider registry primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class ProviderConfig:
    """Describe one Jarvis-capable provider and how it should appear to the system."""

    name: str
    display_name: str
    is_default: bool = False
    enabled: bool = True
    supports_stream: bool = True
    meta: dict[str, Any] = field(default_factory=dict)


class ProviderRegistry:
    """She knows who can speak, and in what voice."""

    def __init__(self):
        self._providers: dict[str, ProviderConfig] = {}
        self._adapters: dict[str, Callable[..., Any] | Any] = {}

    def register(self, config: ProviderConfig, adapter: Callable[..., Any] | Any):
        key = config.name.lower()
        self._providers[key] = config
        self._adapters[key] = adapter

    def get_config(self, name: str | None) -> ProviderConfig | None:
        if not name:
            return self.get_default_config()
        return self._providers.get(name.lower())

    def get(self, name: str | None) -> Callable[..., Any] | Any | None:
        if not name:
            return self.get_default()
        key = name.lower()
        cfg = self._providers.get(key)
        if not cfg or not cfg.enabled:
            return None
        return self._adapters.get(key)

    def get_default(self) -> Callable[..., Any] | Any | None:
        cfg = self.get_default_config()
        if cfg is None:
            return None
        return self._adapters.get(cfg.name.lower())

    def get_default_config(self) -> ProviderConfig | None:
        for cfg in self._providers.values():
            if cfg.is_default and cfg.enabled:
                return cfg
        return None

    def get_default_name(self) -> str | None:
        cfg = self.get_default_config()
        return cfg.name.lower() if cfg else None

    def route_provider(
        self,
        requested: str | None,
        *,
        fallback_name: str | None = None,
    ) -> tuple[Callable[..., Any] | Any | None, str | None]:
        """Resolve the requested provider, then fall back to the enabled default."""
        if requested:
            cfg = self.get_config(requested)
            if cfg and cfg.enabled:
                return self._adapters.get(cfg.name.lower()), cfg.name.lower()

        default_cfg = self.get_default_config()
        if default_cfg and default_cfg.enabled:
            return self._adapters.get(default_cfg.name.lower()), default_cfg.name.lower()

        if fallback_name:
            cfg = self.get_config(fallback_name)
            if cfg and cfg.enabled:
                return self._adapters.get(cfg.name.lower()), cfg.name.lower()

        return None, None

    def is_available(self, name: str) -> bool:
        cfg = self._providers.get(name.lower())
        return bool(cfg and cfg.enabled)

    def list_providers(self) -> dict[str, ProviderConfig]:
        return dict(self._providers)
