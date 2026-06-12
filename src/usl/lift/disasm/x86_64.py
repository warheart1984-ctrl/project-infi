"""Minimal x86_64 linear decoder for P1 lift (ELF Linux)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Literal

InsnKind = Literal["unknown", "nop", "ret", "syscall", "call", "jmp", "other"]


@dataclass
class Instruction:
    vaddr: int
    size: int
    kind: InsnKind
    raw: bytes


def _skip_prefixes(data: bytes, i: int) -> int:
    while i < len(data):
        b = data[i]
        if b in (0x66, 0x67, 0xF0, 0xF2, 0xF3):
            i += 1
            continue
        if b in range(0x40, 0x50):
            i += 1
            continue
        break
    return i


def _decode_one(data: bytes, base_vaddr: int, offset: int) -> Instruction | None:
    if offset >= len(data):
        return None
    start = offset
    i = _skip_prefixes(data, offset)
    if i >= len(data):
        return Instruction(vaddr=base_vaddr + start, size=1, kind="unknown", raw=data[start : start + 1])

    b0 = data[i]

    if b0 == 0x90:
        return Instruction(vaddr=base_vaddr + start, size=i - start + 1, kind="nop", raw=data[start : i + 1])
    if b0 == 0xC3:
        return Instruction(vaddr=base_vaddr + start, size=i - start + 1, kind="ret", raw=data[start : i + 1])
    if b0 == 0x0F and i + 1 < len(data) and data[i + 1] == 0x05:
        return Instruction(vaddr=base_vaddr + start, size=i - start + 2, kind="syscall", raw=data[start : i + 2])
    if b0 == 0xCD and i + 1 < len(data) and data[i + 1] == 0x2E:
        return Instruction(vaddr=base_vaddr + start, size=i - start + 2, kind="syscall", raw=data[start : i + 2])
    if b0 == 0xEB and i + 1 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 2, kind="jmp", raw=data[start : i + 2])
    if b0 == 0xE9 and i + 4 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 5, kind="jmp", raw=data[start : i + 5])
    if b0 == 0xE8 and i + 4 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 5, kind="call", raw=data[start : i + 5])
    if b0 == 0xB8 and i + 4 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 5, kind="other", raw=data[start : i + 5])
    if b0 == 0x48 and i + 2 < len(data) and data[i + 1] == 0xC7 and data[i + 2] == 0xC0 and i + 6 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 7, kind="other", raw=data[start : i + 7])
    if b0 == 0x48 and i + 1 < len(data) and data[i + 1] == 0xB8 and i + 9 < len(data):
        return Instruction(vaddr=base_vaddr + start, size=i - start + 10, kind="other", raw=data[start : i + 10])

    return Instruction(vaddr=base_vaddr + start, size=i - start + 1, kind="unknown", raw=data[start : i + 1])


def decode_instructions(text: bytes, base_vaddr: int) -> list[Instruction]:
    """Linear sweep decode until end of text."""
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
