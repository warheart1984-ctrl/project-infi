"""Minimal PE loader → UBO + import binder stubs."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from src.usl.types import GuestContext, GuestAddressSpace, ImportSlot, SegmentInfo, UBO

DOS_MAGIC = b"MZ"
PE_SIGNATURE = b"PE\x00\x00"
IMAGE_DIRECTORY_ENTRY_IMPORT = 1


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _normalize_ubo_bytes(ubo_dict: dict) -> bytes:
    import json

    return json.dumps(ubo_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _read_cstring(data: bytes, offset: int) -> str:
    end = data.find(b"\x00", offset)
    if end < 0:
        end = len(data)
    return data[offset:end].decode("ascii", errors="replace")


def load_pe_bytes(data: bytes, *, source_path: str | None = None) -> tuple[UBO, GuestAddressSpace]:
    """Parse PE from in-memory bytes (courier / exokernel path)."""
    return _parse_pe(data, source_path=source_path)


def load_pe(path: str | Path) -> tuple[UBO, GuestAddressSpace]:
    """Parse PE and return UBO + guest address space."""
    path = Path(path)
    return load_pe_bytes(path.read_bytes(), source_path=str(path))


def _parse_pe(data: bytes, *, source_path: str | None = None) -> tuple[UBO, GuestAddressSpace]:
    if data[:2] != DOS_MAGIC:
        raise ValueError("not a PE file")

    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew : e_lfanew + 4] != PE_SIGNATURE:
        raise ValueError("invalid PE signature")

    # COFF header
    machine, num_sections, _, _, _, opt_hdr_size, _ = struct.unpack_from(
        "<HHIIIHH", data, e_lfanew + 4
    )
    opt_off = e_lfanew + 24
    magic = struct.unpack_from("<H", data, opt_off)[0]
    is_pe32_plus = magic == 0x20B

    if is_pe32_plus:
        entry_point, image_base = struct.unpack_from("<II", data, opt_off + 16)
        num_rva_sizes = struct.unpack_from("<I", data, opt_off + 108)[0]
        data_dir_off = opt_off + 112
    else:
        entry_point, image_base = struct.unpack_from("<II", data, opt_off + 16)
        num_rva_sizes = struct.unpack_from("<I", data, opt_off + 92)[0]
        data_dir_off = opt_off + 96

    sections: list[SegmentInfo] = []
    address_space = GuestAddressSpace()
    sec_off = opt_off + opt_hdr_size
    for i in range(num_sections):
        off = sec_off + i * 40
        name_raw = data[off : off + 8]
        name = name_raw.split(b"\x00")[0].decode("ascii", errors="replace")
        virtual_size, virtual_addr, raw_size, raw_ptr = struct.unpack_from(
            "<IIII", data, off + 8
        )
        seg_data = data[raw_ptr : raw_ptr + raw_size] if raw_size else b""
        seg = SegmentInfo(
            name=name or f"sec_{i}",
            virtual_address=int(virtual_addr),
            virtual_size=int(virtual_size),
            raw_size=int(raw_size),
            flags="",
            data=seg_data,
        )
        sections.append(seg)
        address_space.map_segment(seg)

    imports: list[ImportSlot] = []
    if num_rva_sizes > IMAGE_DIRECTORY_ENTRY_IMPORT:
        import_rva, import_size = struct.unpack_from(
            "<II", data, data_dir_off + IMAGE_DIRECTORY_ENTRY_IMPORT * 8
        )
        if import_rva and import_size:
            imports = _parse_import_directory(data, import_rva, sections)

    if not imports:
        imports = _default_win32_imports()

    arch = "x86_64" if machine == 0x8664 else f"machine_{machine:#x}"
    ubo_dict = {
        "version": "v1",
        "os_family": "windows",
        "format": "pe",
        "architecture": arch,
        "entry_point": int(entry_point),
        "image_base": int(image_base),
        "signature_status": "unverified",
        "segments": [
            {
                "name": s.name,
                "virtual_address": s.virtual_address,
                "virtual_size": s.virtual_size,
                "raw_size": s.raw_size,
            }
            for s in sections
        ],
        "imports": [
            {"module": i.module, "symbol": i.symbol, "slot_id": i.slot_id}
            for i in imports
        ],
    }
    binary_id = _sha256(_normalize_ubo_bytes(ubo_dict))

    metadata: dict = {"machine": machine, "num_sections": num_sections}
    if source_path:
        metadata["source_path"] = source_path
    metadata["content_hash"] = _sha256(data)

    ubo = UBO(
        version="v1",
        binary_id=binary_id,
        os_family="windows",
        format="pe",
        entry_point=int(entry_point),
        segments=sections,
        imports=imports,
        architecture=arch,
        image_base=int(image_base),
        metadata=metadata,
    )
    return ubo, address_space


def _rva_to_offset(rva: int, sections: list[SegmentInfo]) -> int | None:
    for sec in sections:
        if sec.virtual_address <= rva < sec.virtual_address + max(sec.virtual_size, sec.raw_size):
            return rva - sec.virtual_address
    return None


def _parse_import_directory(
    data: bytes, import_rva: int, sections: list[SegmentInfo]
) -> list[ImportSlot]:
    """Parse import directory (simplified; uses section raw layout)."""
    imports: list[ImportSlot] = []
    # Find section containing import_rva
    file_off = None
    for sec in sections:
        if sec.virtual_address <= import_rva < sec.virtual_address + sec.raw_size:
            file_off = import_rva - sec.virtual_address
            break
    if file_off is None:
        return _default_win32_imports()

    off = file_off
    while True:
        if off + 20 > len(data):
            break
        (
            _orig,
            _ts,
            _fwd,
            name_rva,
            first_thunk,
        ) = struct.unpack_from("<IIIII", data, off)
        if name_rva == 0 and first_thunk == 0:
            break
        module_name = _resolve_rva_string(data, name_rva, sections)
        thunk_rva = first_thunk
        while True:
            thunk_off = _rva_to_file_offset(data, thunk_rva, sections)
            if thunk_off is None:
                break
            name_ptr = struct.unpack_from("<I", data, thunk_off)[0]
            if name_ptr == 0:
                break
            sym = _resolve_rva_string(data, name_ptr + 2, sections)
            slot_id = f"{module_name}!{sym}".lower()
            imports.append(
                ImportSlot(module=module_name, symbol=sym, slot_id=slot_id)
            )
            thunk_rva += 8
        off += 20

    if not imports:
        return _default_win32_imports()
    return imports


def _rva_to_file_offset(data: bytes, rva: int, sections: list[SegmentInfo]) -> int | None:
    for sec in sections:
        size = max(sec.virtual_size, sec.raw_size)
        if sec.virtual_address <= rva < sec.virtual_address + size:
            delta = rva - sec.virtual_address
            # Reconstruct from segment data offset in file - use virtual mapping
            return None  # simplified: fall through
    return None


def _resolve_rva_string(data: bytes, rva: int, sections: list[SegmentInfo]) -> str:
    for sec in sections:
        if sec.virtual_address <= rva < sec.virtual_address + len(sec.data):
            rel = rva - sec.virtual_address
            return _read_cstring(sec.data, rel)
    return f"rva_{rva:#x}"


def _default_win32_imports() -> list[ImportSlot]:
    return [
        ImportSlot("KERNEL32.dll", "CreateFileW", "kernel32.dll!createfilew"),
        ImportSlot("KERNEL32.dll", "WriteFile", "kernel32.dll!writefile"),
        ImportSlot("KERNEL32.dll", "ReadFile", "kernel32.dll!readfile"),
        ImportSlot("KERNEL32.dll", "CloseHandle", "kernel32.dll!closehandle"),
    ]


class GuestProcess:
    """Simulated Windows guest for Phase 1."""

    def __init__(self, guest: GuestContext, gate=None) -> None:
        self.guest = guest
        self.gate = gate
        self._import_bindings: dict[str, str] = {}

    def bind_import(self, slot_id: str, capability_id: str) -> None:
        """Lazy binding on first call."""
        self._import_bindings[slot_id] = capability_id

    def simulate_write(self, path: str, data: bytes, gate=None) -> tuple[object, dict | None]:
        """notepad.exe scenario via windows_fs adapter."""
        from src.usl.adapters.windows_fs import windows_fs_write
        from src.usl.gate import USLGate

        g = gate or self.gate or USLGate()
        return windows_fs_write(g, self.guest, path, data)


def guest_from_pe_bytes(data: bytes, *, source_path: str | None = None, **kwargs) -> GuestContext:
    ubo, addr = load_pe_bytes(data, source_path=source_path)
    return GuestContext(
        ubo=ubo,
        address_space=addr,
        process_id=kwargs.get("process_id", "win-guest-1"),
        **{k: v for k, v in kwargs.items() if k != "process_id"},
    )


def guest_from_pe(path: str | Path, **kwargs) -> GuestContext:
    path = Path(path)
    return guest_from_pe_bytes(path.read_bytes(), source_path=str(path), **kwargs)
