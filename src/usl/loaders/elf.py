"""Minimal ELF64 loader → UBO + guest address space."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from src.usl.types import GuestAddressSpace, GuestContext, ImportSlot, SegmentInfo, UBO

ELF_MAGIC = b"\x7fELF"
PT_LOAD = 1


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _normalize_ubo_bytes(ubo_dict: dict) -> bytes:
    """Deterministic bytes for binary_id."""
    import json

    return json.dumps(ubo_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_elf_bytes(data: bytes, *, source_path: str | None = None) -> tuple[UBO, GuestAddressSpace]:
    """Parse ELF64 from in-memory bytes (courier / exokernel path)."""
    return _parse_elf64(data, source_path=source_path)


def load_elf(path: str | Path) -> tuple[UBO, GuestAddressSpace]:
    """Parse ELF64 and return UBO + mapped guest address space."""
    path = Path(path)
    return load_elf_bytes(path.read_bytes(), source_path=str(path))


def _parse_elf64(data: bytes, *, source_path: str | None = None) -> tuple[UBO, GuestAddressSpace]:
    """Core ELF64 parser shared by path and bytes loaders."""
    if data[:4] != ELF_MAGIC:
        raise ValueError("not an ELF file")

    ei_class = data[4]
    if ei_class != 2:
        raise ValueError("only ELF64 supported in Phase 1")

    ei_data = data[5]
    endian = "<" if ei_data == 1 else ">"

    (
        e_type,
        e_machine,
        _e_version,
        e_entry,
        e_phoff,
        e_shoff,
        _e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    ) = struct.unpack_from(endian + "HHIQQQIHHHHHH", data, 16)

    segments: list[SegmentInfo] = []
    address_space = GuestAddressSpace()

    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        if e_phentsize < 56:
            continue
        (
            p_type,
            p_flags,
            p_offset,
            p_vaddr,
            p_paddr,
            p_filesz,
            p_memsz,
            _align,
        ) = struct.unpack_from(endian + "IIQQQQQQ", data, off)

        if p_type != PT_LOAD:
            continue

        seg_data = data[p_offset : p_offset + p_filesz]
        name = f"LOAD_{p_vaddr:08x}"
        seg = SegmentInfo(
            name=name,
            virtual_address=int(p_vaddr),
            virtual_size=int(p_memsz),
            raw_size=int(p_filesz),
            flags=f"flags={p_flags:#x}",
            data=seg_data,
        )
        segments.append(seg)
        address_space.map_segment(seg)

    imports: list[ImportSlot] = []
    # Phase 1 stub: syscall binder slots
    for sym in ("open", "read", "write", "exit"):
        imports.append(
            ImportSlot(
                module="libc",
                symbol=sym,
                slot_id=f"libc.{sym}",
            )
        )

    if e_machine == 62:
        arch = "x86_64"
    elif e_machine == 183:  # EM_AARCH64
        arch = "aarch64"
    else:
        arch = f"machine_{e_machine}"
    ubo_dict = {
        "version": "v1",
        "os_family": "linux",
        "format": "elf",
        "architecture": arch,
        "entry_point": int(e_entry),
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
    }
    binary_id = _sha256(_normalize_ubo_bytes(ubo_dict))

    metadata: dict = {"e_type": e_type, "e_phnum": e_phnum, "e_shnum": e_shnum}
    if source_path:
        metadata["source_path"] = source_path
    metadata["content_hash"] = _sha256(data)

    ubo = UBO(
        version="v1",
        binary_id=binary_id,
        os_family="linux",
        format="elf",
        entry_point=int(e_entry),
        segments=segments,
        imports=imports,
        architecture=arch,
        image_base=0,
        metadata=metadata,
    )
    return ubo, address_space


def guest_from_elf(path: str | Path, **kwargs) -> GuestContext:
    """Load ELF and build guest context."""
    ubo, addr = load_elf(path)
    return _guest_from_ubo(ubo, addr, **kwargs)


def guest_from_elf_bytes(
    data: bytes,
    *,
    source_path: str | None = None,
    **kwargs,
) -> GuestContext:
    """Load ELF from raw bytes and build guest context."""
    ubo, addr = load_elf_bytes(data, source_path=source_path)
    return _guest_from_ubo(ubo, addr, **kwargs)


def _guest_from_ubo(ubo: UBO, addr: GuestAddressSpace, **kwargs) -> GuestContext:
    return GuestContext(
        ubo=ubo,
        address_space=addr,
        process_id=kwargs.get("process_id", "elf-guest-1"),
        **{k: v for k, v in kwargs.items() if k != "process_id"},
    )


def syscall_write(
    guest: GuestContext,
    path: str,
    data: bytes,
    gate,
    *,
    broker=None,
) -> tuple[object, dict | None]:
    """ELF syscall binder: write → broker (preferred) or gate."""
    import base64

    if broker is not None:
        from src.usl.broker.ipc import BrokerMessage

        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path=path,
            payload_b64=base64.b64encode(data).decode("ascii"),
            guest_process_id=guest.process_id,
            profile_id=guest.profile_id,
        )
        resp = broker.handle(msg)
        substrate = resp.substrate
        return type("BrokerTransition", (), {"law": type("L", (), {"decision": resp.decision})()})(), substrate

    from src.usl.adapters.windows_fs import build_fs_write_request

    request = build_fs_write_request(guest, path, data)
    request.guest = guest
    return gate.dispatch(request)
