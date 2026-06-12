"""Lift control-flow shape from executable text."""

from __future__ import annotations

from src.usl.lift.disasm import get_disasm_backend
from src.usl.lift.disasm.x86_64 import Instruction
from src.usl.lift.types import (
    ULBasicBlock,
    ULControlEdge,
    ULControlShape,
    ULFunction,
    ULProgramMeta,
)
from src.usl.types import SegmentInfo, UBO


def _text_segment(ubo: UBO) -> SegmentInfo | None:
    for seg in ubo.segments:
        name = (seg.name or "").lower()
        flags = (seg.flags or "").lower()
        if "exec" in flags or "x" in flags or ".text" in name or seg.virtual_address == ubo.entry_point:
            if seg.data:
                return seg
    for seg in ubo.segments:
        if seg.data and seg.virtual_address <= ubo.entry_point < seg.virtual_address + max(seg.virtual_size, len(seg.data)):
            return seg
    return ubo.segments[0] if ubo.segments else None


def _terminator_for(insn: Instruction) -> str:
    if insn.kind == "ret":
        return "return"
    if insn.kind == "syscall":
        return "syscall"
    if insn.kind == "jmp":
        return "branch"
    if insn.kind == "call":
        return "call"
    return "fallthrough"


def lift_control_from_text(ubo: UBO, meta: ULProgramMeta) -> ULControlShape:
    """P1: linear sweep → basic blocks at entry and branch sites."""
    seg = _text_segment(ubo)
    if seg is None or not seg.data:
        return ULControlShape()

    base = seg.virtual_address
    backend = get_disasm_backend(ubo.architecture)
    insns = backend.decode_instructions(seg.data, base)
    if not insns:
        return ULControlShape()

    block_starts = {ubo.entry_point}
    for insn in insns:
        if insn.kind in ("jmp", "call"):
            block_starts.add(insn.vaddr + insn.size)

    sorted_starts = sorted(block_starts)
    start_set = set(sorted_starts)
    blocks: list[ULBasicBlock] = []
    edges: list[ULControlEdge] = []

    insn_by_vaddr = {i.vaddr: i for i in insns}
    vaddrs = [i.vaddr for i in insns]

    for idx, start in enumerate(sorted_starts):
        block_id = f"bb-{start:08x}"
        size = 0
        terminator = "unknown"
        cursor = start
        while cursor in insn_by_vaddr:
            insn = insn_by_vaddr[cursor]
            size += insn.size
            terminator = _terminator_for(insn)
            if terminator != "fallthrough":
                break
            nxt = cursor + insn.size
            if nxt in start_set and nxt != start:
                break
            cursor = nxt

        if size == 0 and start in insn_by_vaddr:
            insn = insn_by_vaddr[start]
            size = insn.size
            terminator = _terminator_for(insn)

        blocks.append(
            ULBasicBlock(
                block_id=block_id,
                start_vaddr=start,
                size=size,
                terminator=terminator,  # type: ignore[arg-type]
            )
        )

        if terminator == "fallthrough" and start + size in start_set:
            edges.append(ULControlEdge(from_block=block_id, to_block=f"bb-{(start + size):08x}", kind="fallthrough"))
        if terminator == "call" and start + size in start_set:
            edges.append(ULControlEdge(from_block=block_id, to_block=f"bb-{(start + size):08x}", kind="call"))

    entry_blocks = [b.block_id for b in blocks if b.start_vaddr == ubo.entry_point]
    functions = [
        ULFunction(
            function_id="fn-entry",
            entry_vaddr=ubo.entry_point,
            blocks=entry_blocks or ([blocks[0].block_id] if blocks else []),
        )
    ]

    return ULControlShape(blocks=blocks, edges=edges, functions=functions)
