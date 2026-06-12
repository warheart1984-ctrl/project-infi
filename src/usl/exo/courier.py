"""Exokernel courier: load → lift → register → forge (no interpretation)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.cloud_forge.types import LawEnvelope
from src.usl.exo.registry import AAISRegistry, get_default_registry
from src.usl.forge.compiler import ForgeCompiler
from src.usl.forge.dynamic_emitter import DynamicForgeBundle
from src.usl.forge.static_emitter import StaticForgeImageRef
from src.usl.lift import lift_machine_code
from src.usl.lift.types import ULLiftedModel
from src.usl.loaders.elf import guest_from_elf_bytes, load_elf_bytes
from src.usl.loaders.pe import guest_from_pe_bytes
from src.usl.types import GuestContext

ELF_MAGIC = b"\x7fELF"
PE_MAGIC = b"MZ"


@dataclass
class LiftRegisterResult:
    model: ULLiftedModel
    artifact_id: str
    forge_output: DynamicForgeBundle | StaticForgeImageRef
    guest: GuestContext


class ExokernelCourier:
    """Thin mux: normalize substrate, delegate lift/forge, register artifact."""

    def __init__(self, registry: AAISRegistry | None = None) -> None:
        self._registry = registry or get_default_registry()

    @staticmethod
    def _normalize_guest(
        raw_bytes: bytes,
        *,
        guest_context: GuestContext | None = None,
        source_path: str | None = None,
    ) -> GuestContext:
        if guest_context is not None:
            return guest_context
        if raw_bytes[:4] == ELF_MAGIC:
            return guest_from_elf_bytes(raw_bytes, source_path=source_path)
        if raw_bytes[:2] == PE_MAGIC:
            return guest_from_pe_bytes(raw_bytes, source_path=source_path)
        raise ValueError("unsupported binary format (expected ELF or PE)")

    @staticmethod
    def _artifact_hash_from_guest(guest: GuestContext) -> str | None:
        meta = guest.ubo.metadata or {}
        return meta.get("content_hash")

    def lift_and_register(
        self,
        raw_bytes: bytes,
        *,
        guest_context: GuestContext | None = None,
        law_envelope: LawEnvelope | None = None,
        domain: str | None = None,
        forge_mode: Literal["dynamic", "static"] = "dynamic",
        source_path: str | None = None,
        rootfs_dir: Path | None = None,
    ) -> LiftRegisterResult:
        guest = self._normalize_guest(
            raw_bytes,
            guest_context=guest_context,
            source_path=source_path,
        )
        law = law_envelope or LawEnvelope(law_id="usl-lift-default", law_version="1")
        artifact_hash = self._artifact_hash_from_guest(guest)
        model = lift_machine_code(
            guest.ubo,
            artifact_hash=artifact_hash,
            source_path=source_path,
        )
        artifact_id = self._registry.register_lifted_model(
            model,
            domain=domain,
            law_envelope=law,
        )
        forge_output = ForgeCompiler.emit(
            model,
            mode=forge_mode,
            law=law,
            domain=domain,
            guest=guest,
            rootfs_dir=rootfs_dir,
        )
        return LiftRegisterResult(
            model=model,
            artifact_id=artifact_id,
            forge_output=forge_output,
            guest=guest,
        )

    @classmethod
    def lift_and_register_from_path(
        cls,
        path: str | Path,
        *,
        law_envelope: LawEnvelope | None = None,
        domain: str | None = None,
        forge_mode: Literal["dynamic", "static"] = "dynamic",
        rootfs_dir: Path | None = None,
        registry: AAISRegistry | None = None,
    ) -> LiftRegisterResult:
        raw = Path(path).read_bytes()
        courier = cls(registry=registry)
        return courier.lift_and_register(
            raw,
            law_envelope=law_envelope,
            domain=domain,
            forge_mode=forge_mode,
            source_path=str(path),
            rootfs_dir=rootfs_dir,
        )
