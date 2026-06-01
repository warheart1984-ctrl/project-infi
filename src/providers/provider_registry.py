"""Compatibility path for the AAIS-native provider registry."""

from src.jarvis_provider_registry import ProviderConfig
from src.provider_registry import ProviderRegistry, provider_registry

__all__ = ["ProviderConfig", "ProviderRegistry", "provider_registry"]
