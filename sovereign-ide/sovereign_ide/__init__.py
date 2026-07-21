"""Importable package facade for Sovereign IDE."""

from .app import build_runtime, build_shell, main
from runtime import (
    SURFACE_DEFINITIONS,
    SovereignIdeApiServer,
    SovereignRuntimeContext,
    SurfaceDefinition,
)

__all__ = [
    "SURFACE_DEFINITIONS",
    "SovereignIdeApiServer",
    "SovereignRuntimeContext",
    "SurfaceDefinition",
    "build_runtime",
    "build_shell",
    "main",
]
