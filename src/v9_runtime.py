"""Inspectable runtime wrapper for the Jarvis V9 core."""

from __future__ import annotations

from pathlib import Path

from .creative_core_runtime import CreativeCoreRuntime, RuntimeMode
from .v9_core import v9_core_engine


class V9Runtime(CreativeCoreRuntime):
    """Bounded V9 runtime wrapper."""

    def __init__(
        self,
        *,
        mode: RuntimeMode = "real",
        runtime_dir: str | Path | None = None,
    ) -> None:
        super().__init__("v9", v9_core_engine, runtime_dir=runtime_dir, mode=mode)


v9_runtime = V9Runtime()
