"""Supervision mode configuration (env-gated, default ipc)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SupervisionConfig:
    mode: str = "ipc"
    guest_elf: str = ""
    guest_process_id: str = "usl-supervised-guest"
    broker_socket: str = ""

    @property
    def uses_ptrace(self) -> bool:
        return self.mode == "ptrace"


def supervision_mode_from_env() -> str:
    """Return ``ipc`` (default) or ``ptrace``."""
    raw = os.environ.get("USL_SUPERVISION_MODE", "ipc").strip().lower()
    if raw in ("ptrace", "ipc"):
        return raw
    return "ipc"


def load_supervision_config() -> SupervisionConfig:
    return SupervisionConfig(
        mode=supervision_mode_from_env(),
        guest_elf=os.environ.get("USL_SUPERVISION_GUEST_ELF", "").strip(),
        guest_process_id=os.environ.get(
            "USL_SUPERVISION_GUEST_ID", "usl-supervised-guest"
        ).strip(),
        broker_socket=os.environ.get("USL_BROKER_SOCKET", "").strip(),
    )
