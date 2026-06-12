"""Universal Substrate Loader (USL) for Nova NorthStar CoG OS."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "USLGate",
    "CapabilityRequest",
    "GuestContext",
    "UBO",
    "VossTransition",
]

if TYPE_CHECKING:
    from src.usl.gate import USLGate
    from src.usl.types import CapabilityRequest, GuestContext, UBO, VossTransition


def __getattr__(name: str):
    if name == "USLGate":
        from src.usl.gate import USLGate

        return USLGate
    if name in ("CapabilityRequest", "GuestContext", "UBO", "VossTransition"):
        from src.usl import types

        return getattr(types, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
