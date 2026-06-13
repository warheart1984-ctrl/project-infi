"""Nova identity declarations for lawful runtime admission."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class NovaIdentity:
    tier: str
    operator_session_id: str
    instance_id: str


def declare_identity(*, tier: str, operator_session_id: str) -> NovaIdentity:
    session = str(operator_session_id or "").strip()
    return NovaIdentity(
        tier=str(tier or "nova").strip() or "nova",
        operator_session_id=session,
        instance_id=f"nova-{uuid4()}",
    )
