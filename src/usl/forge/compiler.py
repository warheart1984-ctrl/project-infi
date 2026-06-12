"""ForgeCompiler: dual-mode emission from ULLiftedModel."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from src.cloud_forge.types import LawEnvelope
from src.usl.forge.dynamic_emitter import DynamicForgeBundle, emit_dynamic
from src.usl.forge.static_emitter import StaticForgeImageRef, emit_static
from src.usl.lift.types import ULLiftedModel
from src.usl.types import GuestContext


class ForgeCompiler:
    @staticmethod
    def emit(
        model: ULLiftedModel,
        *,
        mode: Literal["dynamic", "static"],
        law: LawEnvelope,
        domain: str | None = None,
        guest: GuestContext | None = None,
        rootfs_dir: Path | None = None,
    ) -> DynamicForgeBundle | StaticForgeImageRef:
        del guest  # reserved for runtime binding in later phases
        if mode == "dynamic":
            return emit_dynamic(model, law=law, domain=domain)
        if mode == "static":
            if rootfs_dir is None:
                raise ValueError("rootfs_dir required for static forge emission")
            return emit_static(model, law=law, domain=domain, rootfs_dir=rootfs_dir)
        raise ValueError(f"unknown forge mode: {mode}")
