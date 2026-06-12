"""Build minimal ELF64 and PE64 fixtures for USL loader tests."""

from __future__ import annotations

import struct
import time
from pathlib import Path


def build_minimal_elf64() -> bytes:
    e_ident = bytes(
        [
            0x7F,
            0x45,
            0x4C,
            0x46,
            2,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    e_phoff = 64
    e_entry = 0x400078
    code = b"\x90\xc3"

    hdr = e_ident + struct.pack(
        "<HHIQQQIHHHHHH",
        2,
        62,
        1,
        e_entry,
        e_phoff,
        0,
        0,
        64,
        56,
        1,
        0,
        0,
        0,
    )
    p_offset = len(hdr) + 56
    phdr = struct.pack(
        "<IIQQQQQQ",
        1,
        5,
        p_offset,
        e_entry,
        0,
        len(code),
        len(code),
        0x1000,
    )
    pad = b"\x00" * (p_offset - len(hdr) - len(phdr))
    return hdr + phdr + pad + code


def build_syscall_elf64() -> bytes:
    """ELF64 with mov rax, 1; syscall for lift effects / admission tests."""
    e_ident = bytes(
        [
            0x7F,
            0x45,
            0x4C,
            0x46,
            2,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    e_phoff = 64
    e_entry = 0x400078
    code = bytes.fromhex("48c7c00100000000") + b"\x0f\x05"

    hdr = e_ident + struct.pack(
        "<HHIQQQIHHHHHH",
        2,
        62,
        1,
        e_entry,
        e_phoff,
        0,
        0,
        64,
        56,
        1,
        0,
        0,
        0,
    )
    p_offset = len(hdr) + 56
    phdr = struct.pack(
        "<IIQQQQQQ",
        1,
        5,
        p_offset,
        e_entry,
        0,
        len(code),
        len(code),
        0x1000,
    )
    pad = b"\x00" * (p_offset - len(hdr) - len(phdr))
    return hdr + phdr + pad + code


def build_windows_syscall_pe64() -> bytes:
    """PE64 with mov eax, 1; int 0x2e for Windows lift effects tests."""
    dos = bytearray(128)
    dos[0:2] = b"MZ"
    pe_off = 128
    struct.pack_into("<I", dos, 0x3C, pe_off)

    opt_size = 0xF0
    coff = struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, opt_size, 0x2022)

    opt = bytearray(opt_size)
    struct.pack_into("<H", opt, 0, 0x20B)
    struct.pack_into("<I", opt, 16, 0x1000)
    struct.pack_into("<Q", opt, 24, 0x140000000)
    struct.pack_into("<H", opt, 68, 0x10)
    struct.pack_into("<I", opt, 108, 16)

    sec_off = pe_off + 4 + 20 + opt_size
    raw_ptr = sec_off + 40
    raw_size = 512
    section = bytearray(40)
    section[0:5] = b".text"
    struct.pack_into("<IIII", section, 8, raw_size, 0x1000, raw_size, raw_ptr)
    struct.pack_into("<I", section, 36, 0x60000020)

    code = bytes.fromhex("b801000000cd2e") + b"\x00" * (raw_size - len(bytes.fromhex("b801000000cd2e")))
    return bytes(dos) + b"PE\x00\x00" + coff + bytes(opt) + bytes(section) + code


def build_minimal_aarch64_elf() -> bytes:
    """ELF64 aarch64 with movz x8, #1; svc #0."""
    e_ident = bytes(
        [
            0x7F,
            0x45,
            0x4C,
            0x46,
            2,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    )
    e_phoff = 64
    e_entry = 0x400078
    # movz x8, #1; svc #0
    # movz x8, #1; svc #0 — AArch64 stores instructions little-endian in memory.
    code = bytes.fromhex("280080d2010000d4")

    hdr = e_ident + struct.pack(
        "<HHIQQQIHHHHHH",
        2,
        183,
        1,
        e_entry,
        e_phoff,
        0,
        0,
        64,
        56,
        1,
        0,
        0,
        0,
    )
    p_offset = len(hdr) + 56
    phdr = struct.pack(
        "<IIQQQQQQ",
        1,
        5,
        p_offset,
        e_entry,
        0,
        len(code),
        len(code),
        0x1000,
    )
    pad = b"\x00" * (p_offset - len(hdr) - len(phdr))
    return hdr + phdr + pad + code


def build_minimal_pe64() -> bytes:
    dos = bytearray(128)
    dos[0:2] = b"MZ"
    pe_off = 128
    struct.pack_into("<I", dos, 0x3C, pe_off)

    opt_size = 0xF0
    coff = struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, opt_size, 0x2022)

    opt = bytearray(opt_size)
    struct.pack_into("<H", opt, 0, 0x20B)
    struct.pack_into("<I", opt, 16, 0x1000)
    struct.pack_into("<Q", opt, 24, 0x140000000)
    struct.pack_into("<H", opt, 68, 0x10)
    struct.pack_into("<I", opt, 108, 16)

    sec_off = pe_off + 4 + 20 + opt_size
    raw_ptr = sec_off + 40
    raw_size = 512
    section = bytearray(40)
    section[0:5] = b".text"
    struct.pack_into("<IIII", section, 8, raw_size, 0x1000, raw_size, raw_ptr)
    struct.pack_into("<I", section, 36, 0x60000020)

    code = b"\x90\xc3" + b"\x00" * (raw_size - 2)
    return bytes(dos) + b"PE\x00\x00" + coff + bytes(opt) + bytes(section) + code


def _atomic_write(path: Path, data: bytes, *, retries: int = 10) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    last_err: OSError | None = None
    for attempt in range(retries):
        try:
            tmp.replace(path)
            return
        except OSError as exc:
            last_err = exc
            if attempt + 1 >= retries:
                raise
            time.sleep(0.02 * (attempt + 1))
    if last_err is not None:
        raise last_err


def _write_if_changed(path: Path, data: bytes) -> None:
    if path.exists() and path.read_bytes() == data:
        return
    _atomic_write(path, data)


def ensure_fixtures(directory: Path | None = None) -> tuple[Path, Path]:
    root = directory or Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    elf_path = root / "minimal.elf"
    pe_path = root / "minimal.pe"
    _write_if_changed(elf_path, build_minimal_elf64())
    _write_if_changed(pe_path, build_minimal_pe64())
    return elf_path, pe_path


def ensure_syscall_elf(directory: Path | None = None) -> Path:
    root = directory or Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / "syscall.elf"
    _write_if_changed(path, build_syscall_elf64())
    return path


def ensure_windows_syscall_pe(directory: Path | None = None) -> Path:
    root = directory or Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / "syscall.pe"
    _write_if_changed(path, build_windows_syscall_pe64())
    return path


def ensure_aarch64_elf(directory: Path | None = None) -> Path:
    root = directory or Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / "minimal.aarch64.elf"
    _write_if_changed(path, build_minimal_aarch64_elf())
    return path


if __name__ == "__main__":
    elf, pe = ensure_fixtures()
    syscall = ensure_syscall_elf()
    win_pe = ensure_windows_syscall_pe()
    aarch64 = ensure_aarch64_elf()
    print(f"wrote {elf} ({elf.stat().st_size} bytes)")
    print(f"wrote {pe} ({pe.stat().st_size} bytes)")
    print(f"wrote {syscall} ({syscall.stat().st_size} bytes)")
    print(f"wrote {win_pe} ({win_pe.stat().st_size} bytes)")
    print(f"wrote {aarch64} ({aarch64.stat().st_size} bytes)")
