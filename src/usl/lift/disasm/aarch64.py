"""Minimal aarch64 linear decoder for P3 lift (ELF Linux)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Literal

InsnKind = Literal["unknown", "nop", "ret", "syscall", "call", "jmp", "other"]

# Re-export shared Instruction shape via x86_64 module (same dataclass fields).
from src.usl.lift.disasm.x86_64 import Instruction  # noqa: E402


def _decode_one(data: bytes, base_vaddr: int, offset: int) -> Instruction | None:
    if offset + 4 > len(data):
        if offset < len(data):
            return Instruction(
                vaddr=base_vaddr + offset,
                size=1,
                kind="unknown",
                raw=data[offset : offset + 1],
            )
        return None

    word = int.from_bytes(data[offset : offset + 4], "little")

    # RET: D65F03C0
    if word == 0xD65F03C0:
        return Instruction(
            vaddr=base_vaddr + offset,
            size=4,
            kind="ret",
            raw=data[offset : offset + 4],
        )
    # NOP: D503201F
    if word == 0xD503201F:
        return Instruction(
            vaddr=base_vaddr + offset,
            size=4,
            kind="nop",
            raw=data[offset : offset + 4],
        )
    # SVC #imm (syscall): top bits 11010100 -> 0xD4xxxxxx
    if (word & 0xFFE0001F) == 0xD4000001 or (word & 0xFFC00000) == 0xD4000000:
        return Instruction(
            vaddr=base_vaddr + offset,
            size=4,
            kind="syscall",
            raw=data[offset : offset + 4],
        )
    # MOVZ/MOVK X8 pattern (heuristic for syscall number setup)
    if (word & 0xFFE0001F) == 0xD2800008:
        return Instruction(
            vaddr=base_vaddr + offset,
            size=4,
            kind="other",
            raw=data[offset : offset + 4],
        )

    return Instruction(
        vaddr=base_vaddr + offset,
        size=4,
        kind="unknown",
        raw=data[offset : offset + 4],
    )


def decode_instructions(text: bytes, base_vaddr: int) -> list[Instruction]:
    out: list[Instruction] = []
    offset = 0
    while offset < len(text):
        insn = _decode_one(text, base_vaddr, offset)
        if insn is None:
            break
        out.append(insn)
        offset += insn.size
    return out


def iter_instructions(text: bytes, base_vaddr: int) -> Iterator[Instruction]:
    yield from decode_instructions(text, base_vaddr)


class LinearAarch64Backend:
    name = "linear_aarch64"

    def decode_instructions(self, text: bytes, base_vaddr: int) -> list[Instruction]:
        return decode_instructions(text, base_vaddr)

    def iter_instructions(self, text: bytes, base_vaddr: int) -> Iterator[Instruction]:
        yield from iter_instructions(text, base_vaddr)
