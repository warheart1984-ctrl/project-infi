"""Disassembly backend protocol for pluggable instruction decoding."""

from __future__ import annotations

import os
from typing import Iterator, Protocol

from src.usl.lift.disasm.x86_64 import Instruction


class DisasmBackend(Protocol):
    name: str

    def decode_instructions(self, text: bytes, base_vaddr: int) -> list[Instruction]:
        ...

    def iter_instructions(self, text: bytes, base_vaddr: int) -> Iterator[Instruction]:
        ...


def _normalize_architecture(architecture: str) -> str:
    arch = (architecture or "x86_64").lower()
    if arch in ("arm64", "aarch64"):
        return "aarch64"
    return arch


def get_disasm_backend(architecture: str) -> DisasmBackend:
    """Resolve disasm backend from architecture and USL_DISASM_BACKEND env."""
    arch = _normalize_architecture(architecture)
    backend_name = os.environ.get("USL_DISASM_BACKEND", "linear").lower()

    if backend_name == "capstone":
        try:
            from src.usl.lift.disasm.capstone_backend import capstone_backend_for

            return capstone_backend_for(arch)
        except ImportError:
            pass

    if arch == "aarch64":
        from src.usl.lift.disasm.aarch64 import LinearAarch64Backend

        return LinearAarch64Backend()

    from src.usl.lift.disasm.linear_x86_64 import LinearX86_64Backend

    return LinearX86_64Backend()
