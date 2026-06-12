"""Lift syscall effects from control + text (P1 Linux x86_64)."""

from __future__ import annotations

from src.usl.lift.disasm import get_disasm_backend
from src.usl.lift.types import (
    AAISEffectSurface,
    Confidence,
    EffectBucket,
    ImportEffect,
    SyscallEffect,
    ULControlShape,
)
from src.usl.types import SegmentInfo, UBO

# Subset of Linux x86_64 syscall numbers → name + bucket
_LINUX_SYSCALLS: dict[int, tuple[str, EffectBucket]] = {
    0: ("read", "fs"),
    1: ("write", "fs"),
    2: ("open", "fs"),
    3: ("close", "fs"),
    4: ("stat", "fs"),
    5: ("fstat", "fs"),
    8: ("lseek", "fs"),
    9: ("mmap", "mem"),
    10: ("mprotect", "mem"),
    11: ("munmap", "mem"),
    12: ("brk", "mem"),
    39: ("getpid", "proc"),
    41: ("socket", "net"),
    42: ("connect", "net"),
    43: ("accept", "net"),
    44: ("sendto", "net"),
    45: ("recvfrom", "net"),
    46: ("sendmsg", "net"),
    47: ("recvmsg", "net"),
    56: ("clone", "proc"),
    57: ("fork", "proc"),
    59: ("execve", "proc"),
    60: ("exit", "proc"),
    61: ("wait4", "proc"),
    62: ("kill", "proc"),
    102: ("getuid", "proc"),
    202: ("futex", "timer"),
    228: ("clock_gettime", "timer"),
    231: ("exit_group", "proc"),
}


def _text_segment(ubo: UBO) -> SegmentInfo | None:
    for seg in ubo.segments:
        if seg.data:
            if seg.virtual_address <= ubo.entry_point < seg.virtual_address + max(seg.virtual_size, len(seg.data)):
                return seg
    return ubo.segments[0] if ubo.segments else None


def _guess_syscall_number_aarch64(text: bytes, syscall_offset: int) -> tuple[int | None, Confidence]:
    """Scan backward for movz x8, #imm before svc."""
    window_start = max(0, syscall_offset - 32)
    window = text[window_start:syscall_offset]
    for i in range(len(window) - 4, -1, -4):
        if i < 0:
            break
        word = int.from_bytes(window[i : i + 4], "little")
        if (word & 0xFFE0001F) == 0xD2800008:
            imm = (word >> 5) & 0xFFFF
            return imm, "proven"
    return None, "unknown"


def _guess_syscall_number(
    text: bytes,
    syscall_offset: int,
    *,
    architecture: str = "x86_64",
) -> tuple[int | None, Confidence]:
    """Scan backward for syscall number setup before syscall/svc."""
    arch = (architecture or "x86_64").lower()
    if arch in ("aarch64", "arm64"):
        return _guess_syscall_number_aarch64(text, syscall_offset)

    window_start = max(0, syscall_offset - 24)
    window = text[window_start:syscall_offset]

    for i in range(len(window) - 4, -1, -1):
        if window[i] == 0xB8 and i + 4 < len(window):
            num = int.from_bytes(window[i + 1 : i + 5], "little")
            return num, "proven"

    for i in range(len(window) - 6, -1, -1):
        if window[i] == 0x48 and window[i + 1] == 0xC7 and window[i + 2] == 0xC0 and i + 6 < len(window):
            num = int.from_bytes(window[i + 3 : i + 7], "little", signed=True) & 0xFFFFFFFF
            return num, "heuristic"

    return None, "unknown"


def _block_for_vaddr(control: ULControlShape, vaddr: int) -> str | None:
    for block in control.blocks:
        if block.start_vaddr <= vaddr < block.start_vaddr + block.size:
            return block.block_id
    return None


def _classify_syscall(
    ubo: UBO,
    *,
    num: int | None,
    confidence: Confidence,
) -> tuple[str | None, EffectBucket]:
    if num is None:
        return None, "unknown"
    if ubo.os_family == "windows":
        # P2: heuristic Windows NT syscall numbers share Linux-like low IDs for fs/proc.
        if num in _LINUX_SYSCALLS:
            name, bucket = _LINUX_SYSCALLS[num]
            return name, bucket
        return None, "unknown"
    if num in _LINUX_SYSCALLS:
        name, bucket = _LINUX_SYSCALLS[num]
        return name, bucket
    return None, "unknown"


def lift_effects_from_syscalls(ubo: UBO, control: ULControlShape) -> AAISEffectSurface:
    """Scan .text for syscall sites and classify syscall buckets (Linux/Windows)."""
    seg = _text_segment(ubo)
    syscalls: list[SyscallEffect] = []
    if seg is None or not seg.data:
        return AAISEffectSurface(syscalls=syscalls, imports=_imports_from_ubo(ubo))

    base = seg.virtual_address
    text = seg.data
    backend = get_disasm_backend(ubo.architecture)
    insns = backend.decode_instructions(text, base)

    effect_idx = 0
    for insn in insns:
        if insn.kind != "syscall":
            continue
        rel_off = insn.vaddr - base
        num, confidence = _guess_syscall_number(text, rel_off, architecture=ubo.architecture)
        name, bucket = _classify_syscall(ubo, num=num, confidence=confidence)

        syscalls.append(
            SyscallEffect(
                effect_id=f"fx-syscall-{effect_idx}",
                syscall_number=num,
                syscall_name=name,
                bucket=bucket,
                confidence=confidence,
                site_vaddr=insn.vaddr,
                block_id=_block_for_vaddr(control, insn.vaddr),
            )
        )
        effect_idx += 1

    return AAISEffectSurface(syscalls=syscalls, imports=_imports_from_ubo(ubo))


def _imports_from_ubo(ubo: UBO) -> list[ImportEffect]:
    return [
        ImportEffect(module=i.module, symbol=i.symbol, slot_id=i.slot_id or f"{i.module}.{i.symbol}")
        for i in ubo.imports
    ]
