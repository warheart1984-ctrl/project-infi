"""Kernel syscall interception bridge (metal) → guest broker."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from src.usl.broker.ipc import BrokerMessage

if TYPE_CHECKING:
    from src.usl.broker.supervisor import GuestBroker


def iter_kernel_events(path: Path) -> Iterator[dict]:
    """Read NDJSON syscall events from kernel stub ingest."""
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def kernel_event_to_message(event: dict, *, profile_id: str = "daily-driver") -> BrokerMessage | None:
    """Map kernel stub event to broker IPC message."""
    syscall = str(event.get("syscall") or event.get("name") or "")
    if syscall in ("write", "pwrite64"):
        return BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path=str(event.get("path") or event.get("pathname") or "/guest/write"),
            payload_b64=str(event.get("payload_b64") or ""),
            guest_process_id=str(event.get("pid") or event.get("guest_process_id") or "kernel-guest"),
            profile_id=profile_id,
            extra={"source": "kernel_stub", "syscall": syscall},
        )
    if syscall in ("connect", "socket"):
        host = str(event.get("host") or "127.0.0.1")
        port = int(event.get("port") or 0)
        return BrokerMessage(
            msg_type="syscall",
            capability_id="net.connect",
            ceiling_id="net.basic",
            path=f"{host}:{port}",
            guest_process_id=str(event.get("pid") or "kernel-guest"),
            profile_id=profile_id,
            extra={"source": "kernel_stub", "syscall": syscall, "host": host, "port": port},
        )
    return None


def drain_kernel_to_broker(
    broker: GuestBroker,
    ingest_path: Path,
    *,
    profile_id: str = "daily-driver",
    max_events: int = 1000,
) -> list[dict]:
    """Process kernel NDJSON ingest through broker; returns result summaries."""
    results: list[dict] = []
    for idx, event in enumerate(iter_kernel_events(ingest_path)):
        if idx >= max_events:
            break
        msg = kernel_event_to_message(event, profile_id=profile_id)
        if msg is None:
            continue
        resp = broker.handle(msg)
        results.append(
            {
                "syscall": event.get("syscall"),
                "ok": resp.ok,
                "decision": resp.decision,
                "transition_id": resp.transition_id,
                "error": resp.error,
            }
        )
    return results
