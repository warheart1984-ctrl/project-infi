"""Windows CreateFileW/WriteFile → USL fs.write adapter."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from src.usl.gate import USLGate
from src.usl.types import (
    CapabilityRequest,
    DeltaSummary,
    GuestContext,
    ResourceInfo,
)
from src.usl.voss_ledger import GENESIS_ROOT


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def build_fs_write_request(
    guest: GuestContext,
    path: str,
    data: bytes,
    *,
    mode: str = "create_or_truncate",
    pre_state_hash: str | None = None,
    transition_id: str | None = None,
    timestamp: str | None = None,
) -> CapabilityRequest:
    """Map Windows write semantics to USL fs.write capability request."""
    pre = pre_state_hash or GENESIS_ROOT
    delta = _sha256(data)
    post = _sha256(pre.encode("utf-8") + delta.encode("utf-8") + path.encode("utf-8"))

    resource = ResourceInfo(
        kind="file",
        locator=path,
        extra={
            "method": "writefile",
            "mode": mode,
            "direction": "outbound",
            "_payload": data,
        },
    )
    return CapabilityRequest(
        capability_id="fs.write",
        ceiling_id="fs.basic",
        resource=resource,
        guest=guest,
        pre_state_hash=pre,
        post_state_hash=post,
        delta_hash=delta,
        delta_summary=DeltaSummary(bytes_written=len(data), objects_created=1),
        transition_id=transition_id,
        timestamp=timestamp,
    )


def windows_fs_write(
    gate: USLGate,
    guest: GuestContext,
    path: str,
    data: bytes,
    *,
    mode: str = "create_or_truncate",
) -> tuple[object, dict | None]:
    """Execute governed fs.write for a Windows guest."""
    request = build_fs_write_request(guest, path, data, mode=mode)
    return gate.dispatch(request)


def notepad_write_example(guest: GuestContext, gate: USLGate | None = None) -> tuple[object, dict | None]:
    """Golden notepad.exe scenario: write 'hello' to test.txt."""
    g = gate or USLGate()
    return windows_fs_write(
        g,
        guest,
        "C:/Users/jon/test.txt",
        b"hello",
        mode="create_or_truncate",
    )
