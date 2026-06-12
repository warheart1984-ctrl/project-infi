"""Minimal Mach-O64 loader → UBO + guest address space."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from src.usl.types import GuestAddressSpace, GuestContext, ImportSlot, SegmentInfo, UBO

MH_MAGIC_64 = 0xFEEDFACF
LC_SEGMENT_64 = 0x19


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _normalize_ubo_bytes(ubo_dict: dict) -> bytes:
    import json

    return json.dumps(ubo_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_macho(path: str | Path) -> tuple[UBO, GuestAddressSpace]:
    """Parse thin Mach-O64 and return UBO + mapped guest address space."""
    data = Path(path).read_bytes()
    if len(data) < 32:
        raise ValueError("truncated mach-o")

    magic, cputype, _cpusub, filetype, ncmds, sizeofcmds, _flags = struct.unpack_from(
        "<IIIIIIII", data, 0
    )
    if magic != MH_MAGIC_64:
        raise ValueError("not Mach-O64")

    segments: list[SegmentInfo] = []
    address_space = GuestAddressSpace()
    off = 32
    for _ in range(ncmds):
        if off + 8 > len(data):
            break
        cmd, cmdsize = struct.unpack_from("<II", data, off)
        if cmd == LC_SEGMENT_64 and cmdsize >= 72:
            segname = data[off + 8 : off + 24].split(b"\x00", 1)[0].decode("ascii", errors="replace")
            vmaddr, vmsize, fileoff, filesize = struct.unpack_from("<QQQQ", data, off + 32)
            seg_data = data[fileoff : fileoff + filesize] if filesize else b""
            seg = SegmentInfo(
                name=segname or "SEG",
                virtual_address=int(vmaddr),
                virtual_size=int(vmsize),
                raw_size=int(filesize),
                flags="macho",
                data=seg_data,
            )
            segments.append(seg)
            address_space.map_segment(seg)
        off += cmdsize

    imports = [
        ImportSlot("libSystem", sym, f"libsystem.{sym}")
        for sym in ("open", "read", "write", "exit")
    ]

    arch = "x86_64" if cputype == 0x01000007 else f"cputype_{cputype:#x}"
    ubo_dict = {
        "version": "v1",
        "os_family": "darwin",
        "format": "macho",
        "architecture": arch,
        "entry_point": 0,
        "image_base": 0,
        "signature_status": "unverified",
        "segments": [
            {
                "name": s.name,
                "virtual_address": s.virtual_address,
                "virtual_size": s.virtual_size,
                "raw_size": s.raw_size,
                "flags": s.flags,
            }
            for s in segments
        ],
        "imports": [
            {"module": i.module, "symbol": i.symbol, "slot_id": i.slot_id}
            for i in imports
        ],
        "metadata": {"filetype": filetype, "ncmds": ncmds},
    }
    binary_id = _sha256(_normalize_ubo_bytes(ubo_dict))

    ubo = UBO(
        version="v1",
        binary_id=binary_id,
        os_family="darwin",
        format="macho",
        entry_point=0,
        segments=segments,
        imports=imports,
        architecture=arch,
        metadata={"filetype": filetype, "ncmds": ncmds},
    )
    return ubo, address_space


def guest_from_macho(path: str | Path, **kwargs) -> GuestContext:
    ubo, addr = load_macho(path)
    return GuestContext(
        ubo=ubo,
        address_space=addr,
        process_id=kwargs.get("process_id", "macho-guest-1"),
        **{k: v for k, v in kwargs.items() if k != "process_id"},
    )
