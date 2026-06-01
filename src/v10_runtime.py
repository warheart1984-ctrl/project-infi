"""Inspectable runtime wrapper for the Jarvis V10 creative core."""

from .creative_core_runtime import CreativeCoreRuntime, RuntimeMode
from .v10_core import v10_core_engine


class V10Runtime(CreativeCoreRuntime):
    def __init__(self, *, mode: RuntimeMode = "real", runtime_dir=None):
        super().__init__("v10", v10_core_engine, runtime_dir=runtime_dir, mode=mode)



v10_runtime = V10Runtime()
