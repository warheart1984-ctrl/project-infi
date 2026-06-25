"""Registry of T0-promoted sensor adapter classes."""

from __future__ import annotations

from typing import Dict, Optional, Type

from .t0_sensor import NTIAAdapter

_REGISTRY: Dict[str, Type] = {
    "NTIAAdapter": NTIAAdapter,
}


def get_t0_sensor_class(cbid: str) -> Optional[Type]:
    return _REGISTRY.get(cbid)


def register_t0_sensor(name: str, cls: Type) -> None:
    _REGISTRY[name] = cls
