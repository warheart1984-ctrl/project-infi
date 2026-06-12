"""Linear sweep x86_64 backend (default)."""

from __future__ import annotations

from typing import Iterator

from src.usl.lift.disasm.x86_64 import Instruction, decode_instructions, iter_instructions


class LinearX86_64Backend:
    name = "linear_x86_64"

    def decode_instructions(self, text: bytes, base_vaddr: int) -> list[Instruction]:
        return decode_instructions(text, base_vaddr)

    def iter_instructions(self, text: bytes, base_vaddr: int) -> Iterator[Instruction]:
        yield from iter_instructions(text, base_vaddr)
