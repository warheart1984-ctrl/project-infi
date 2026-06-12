"""USL Forge lift compiler — dynamic and static emission."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "DynamicForgeBundle",
    "ForgeCompiler",
    "StaticForgeImageRef",
    "emit_dynamic",
    "emit_static",
]

if TYPE_CHECKING:
    from src.usl.forge.compiler import ForgeCompiler
    from src.usl.forge.dynamic_emitter import DynamicForgeBundle, emit_dynamic
    from src.usl.forge.static_emitter import StaticForgeImageRef, emit_static


def __getattr__(name: str):
    if name == "ForgeCompiler":
        from src.usl.forge.compiler import ForgeCompiler

        return ForgeCompiler
    if name == "DynamicForgeBundle":
        from src.usl.forge.dynamic_emitter import DynamicForgeBundle

        return DynamicForgeBundle
    if name == "emit_dynamic":
        from src.usl.forge.dynamic_emitter import emit_dynamic

        return emit_dynamic
    if name == "StaticForgeImageRef":
        from src.usl.forge.static_emitter import StaticForgeImageRef

        return StaticForgeImageRef
    if name == "emit_static":
        from src.usl.forge.static_emitter import emit_static

        return emit_static
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
