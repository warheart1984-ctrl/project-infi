"""Optional Capstone-backed disassembly (USL_DISASM_BACKEND=capstone)."""

from __future__ import annotations

from typing import Iterator

from src.usl.lift.disasm.x86_64 import Instruction, InsnKind

_KIND_MAP: dict[str, InsnKind] = {
    "nop": "nop",
    "ret": "ret",
    "syscall": "syscall",
    "svc": "syscall",
    "call": "call",
    "jmp": "jmp",
}


def _kind_from_mnemonic(mnemonic: str) -> InsnKind:
    m = mnemonic.lower()
    if m in _KIND_MAP:
        return _KIND_MAP[m]
    if m.startswith("b") and m not in ("bic", "bics"):
        return "jmp"
    return "other"


def capstone_backend_for(architecture: str) -> "CapstoneBackend":
    try:
        import capstone  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "capstone package required for USL_DISASM_BACKEND=capstone"
        ) from exc

    arch = architecture.lower()
    if arch in ("aarch64", "arm64"):
        cs_arch = capstone.CS_ARCH_ARM64
        cs_mode = capstone.CS_MODE_ARM
    else:
        cs_arch = capstone.CS_ARCH_X86
        cs_mode = capstone.CS_MODE_64

    return CapstoneBackend(cs_arch=cs_arch, cs_mode=cs_mode, name=f"capstone_{arch}")


class CapstoneBackend:
    def __init__(self, *, cs_arch: int, cs_mode: int, name: str) -> None:
        import capstone  # type: ignore[import-untyped]

        self.name = name
        self._md = capstone.Cs(cs_arch, cs_mode)
        self._md.detail = False

    def decode_instructions(self, text: bytes, base_vaddr: int) -> list[Instruction]:
        return list(self.iter_instructions(text, base_vaddr))

    def iter_instructions(self, text: bytes, base_vaddr: int) -> Iterator[Instruction]:
        for insn in self._md.disasm(text, base_vaddr):
            kind = _kind_from_mnemonic(insn.mnemonic)
            yield Instruction(
                vaddr=int(insn.address),
                size=int(insn.size),
                kind=kind,
                raw=bytes(insn.bytes),
            )
