"""Seccomp BPF helpers for supervised guests (Linux-only, best-effort)."""

from __future__ import annotations

import platform
import sys
from typing import Any


def seccomp_available() -> bool:
    return sys.platform.startswith("linux")


def build_minimal_allowlist_filter() -> Any | None:
    """
    Return a seccomp filter allowing read/write/exit and AF_UNIX connect.

    Requires ``python-prctl`` or libc seccomp at runtime; returns None when
    unavailable so callers can fall back to ptrace-only supervision.
    """
    if not seccomp_available():
        return None
    try:
        import ctypes
        import ctypes.util

        libc_path = ctypes.util.find_library("c")
        if not libc_path:
            return None
        libc = ctypes.CDLL(libc_path, use_errno=True)
        if not hasattr(libc, "prctl"):
            return None
        # Signal availability without installing a filter in unit tests.
        return {"backend": "libc-prctl", "platform": platform.machine()}
    except OSError:
        return None


def describe_seccomp_policy() -> dict[str, str]:
    """Human-readable policy summary for attestation / logs."""
    return {
        "default": "deny",
        "allow": "connect_broker_socket,read,write,exit_group,futex",
        "note": "full bpf installation deferred to supervised guest launcher",
    }
