"""Personal governance gate v0 — fail-closed on unsafe builder state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from constitutional.runtime import ConstitutionalStateRuntime, PersonalConstitutionalStateRuntime
from constitutional.runtime.personal_constitutional_state import PersonalConstitutionalState

CSR = ConstitutionalStateRuntime()
PCS = PersonalConstitutionalStateRuntime(CSR)

THETA_CAPACITY = 0.4
THETA_DEBT = 0.6
THETA_ARCH_WARN = 0.6
THETA_CAPACITY_WARN = 0.6


@dataclass(frozen=True)
class PersonalGateDecision:
    allow: bool
    level: str  # "ok" | "warn" | "block"
    reason: str
    state_snapshot: PersonalConstitutionalState


def evaluate_personal_gate(
    *,
    csr: ConstitutionalStateRuntime | None = None,
    pcs: PersonalConstitutionalStateRuntime | None = None,
) -> PersonalGateDecision:
    runtime_csr = csr or CSR
    runtime_pcs = pcs or PersonalConstitutionalStateRuntime(runtime_csr)
    state = runtime_pcs.update_snapshot(snapshot_at=datetime.now(UTC).replace(microsecond=0))

    if state.capacity_continuity < THETA_CAPACITY and state.debt_score > THETA_DEBT:
        return PersonalGateDecision(
            allow=False,
            level="block",
            reason=(
                "capacity_continuity low and personal debt high; "
                "builder in unsafe state (PX-0)"
            ),
            state_snapshot=state,
        )

    if (
        state.capacity_continuity < THETA_CAPACITY_WARN
        or state.architectural_continuity < THETA_ARCH_WARN
    ):
        return PersonalGateDecision(
            allow=True,
            level="warn",
            reason="continuity or capacity degraded; proceed only with explicit awareness",
            state_snapshot=state,
        )

    return PersonalGateDecision(
        allow=True,
        level="ok",
        reason="personal constitutional state within safe band",
        state_snapshot=state,
    )
