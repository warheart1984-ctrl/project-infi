"""Supervision runner — ptrace loop translating traps to broker messages."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable

from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.supervision.config import SupervisionConfig, load_supervision_config
from src.usl.supervision.seccomp import describe_seccomp_policy


@dataclass
class SupervisionState:
    pid: int | None = None
    traps_handled: int = 0
    running: bool = False
    last_error: str = ""


@dataclass
class SupervisionRunner:
    """
    Spawn a guest and (when mode=ptrace) observe syscalls.

    Production ptrace uses ``PTRACE_SYSCALL``; tests inject traps via
    ``simulate_trap`` without a live child process.
    """

    config: SupervisionConfig = field(default_factory=load_supervision_config)
    state: SupervisionState = field(default_factory=SupervisionState)
    _broker_handle: Callable[[BrokerMessage], BrokerResponse] | None = None

    def attach_broker(self, handler: Callable[[BrokerMessage], BrokerResponse]) -> None:
        self._broker_handle = handler

    def start_guest(self, elf_path: str | None = None) -> int:
        path = elf_path or self.config.guest_elf
        if not path or not os.path.isfile(path):
            raise FileNotFoundError(f"supervision guest elf missing: {path}")
        if self.config.mode != "ptrace":
            raise RuntimeError("start_guest requires USL_SUPERVISION_MODE=ptrace")
        if not sys.platform.startswith("linux"):
            raise OSError("ptrace supervision is Linux-only")

        proc = subprocess.Popen(
            [path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.state.pid = proc.pid
        self.state.running = True
        return proc.pid

    def trap_to_message(
        self,
        *,
        syscall_number: int,
        capability_id: str = "fs.write",
        ceiling_id: str = "fs.basic",
        path: str = "",
        payload_b64: str = "",
    ) -> BrokerMessage:
        return BrokerMessage(
            msg_type="syscall",
            capability_id=capability_id,
            ceiling_id=ceiling_id,
            path=path,
            payload_b64=payload_b64,
            guest_process_id=self.config.guest_process_id,
            profile_id="usl-lifted-guest",
            extra={"syscall_number": syscall_number, "supervision": "ptrace"},
        )

    def handle_trap(
        self,
        syscall_number: int,
        *,
        capability_id: str = "fs.write",
        ceiling_id: str = "fs.basic",
        path: str = "",
        payload_b64: str = "",
    ) -> BrokerResponse:
        if self._broker_handle is None:
            return BrokerResponse(ok=False, decision="error", error="no_broker_attached")
        msg = self.trap_to_message(
            syscall_number=syscall_number,
            capability_id=capability_id,
            ceiling_id=ceiling_id,
            path=path,
            payload_b64=payload_b64,
        )
        resp = self._broker_handle(msg)
        self.state.traps_handled += 1
        return resp

    def smoke_once(self) -> BrokerResponse:
        """Deterministic smoke without ptrace (write syscall number 1 on x86_64 linux)."""
        return self.handle_trap(1, path="/tmp/usl-supervision-smoke.txt", payload_b64="")

    def policy_summary(self) -> dict[str, object]:
        return {
            "mode": self.config.mode,
            "seccomp": describe_seccomp_policy(),
            "guest_process_id": self.config.guest_process_id,
            "traps_handled": self.state.traps_handled,
        }
