"""Sovereign IDE scaffold."""

try:  # pragma: no cover - import path differs under pytest collection
    from .runtime.orchestrator import SovereignRuntimeOrchestrator
    from .runtime.codex_loader import CodexLoader
    from .runtime.api_server import SovereignIdeApiServer
    from .runtime.federation_bootstrapper import FederationBootstrapper
    from .runtime.state import SURFACE_DEFINITIONS, SovereignRuntimeContext, SurfaceDefinition
    from .plugins.prime_architect import PrimeArchitectPlugin
except ImportError:  # pragma: no cover
    from runtime.orchestrator import SovereignRuntimeOrchestrator
    from runtime.codex_loader import CodexLoader
    from runtime.api_server import SovereignIdeApiServer
    from runtime.federation_bootstrapper import FederationBootstrapper
    from runtime.state import SURFACE_DEFINITIONS, SovereignRuntimeContext, SurfaceDefinition
    from plugins.prime_architect import PrimeArchitectPlugin

__all__ = [
    "SURFACE_DEFINITIONS",
    "CodexLoader",
    "FederationBootstrapper",
    "PrimeArchitectPlugin",
    "SovereignRuntimeContext",
    "SovereignRuntimeOrchestrator",
    "SurfaceDefinition",
    "SovereignIdeApiServer",
]
