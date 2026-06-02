"""Platform Membrane - multi-tenant SaaS ingress for governed subsystems.

This package intentionally owns the historical ``platform.*`` namespace used by
the Platform Membrane tests and runtime. Because that shadows Python's standard
library module of the same name, expose the stdlib module's public attributes as
a compatibility surface for third-party packages that call ``platform.system()``
or similar helpers during import.
"""

from __future__ import annotations

import importlib.util
import sysconfig
from pathlib import Path
from types import ModuleType
from typing import Any

__version__ = "1.0.0"


def _load_stdlib_platform() -> ModuleType:
    stdlib_platform = Path(sysconfig.get_path("stdlib")) / "platform.py"
    spec = importlib.util.spec_from_file_location("_aais_stdlib_platform", stdlib_platform)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Python stdlib platform module from {stdlib_platform}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_STDLIB_PLATFORM = _load_stdlib_platform()


def __getattr__(name: str) -> Any:
    return getattr(_STDLIB_PLATFORM, name)


for _name in (
    "architecture",
    "machine",
    "node",
    "platform",
    "processor",
    "python_build",
    "python_compiler",
    "python_implementation",
    "python_version",
    "python_version_tuple",
    "release",
    "system",
    "uname",
    "version",
):
    globals()[_name] = getattr(_STDLIB_PLATFORM, _name)


__all__ = ["__version__"]
