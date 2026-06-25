from __future__ import annotations

from pydantic import BaseModel

from constitutional.core.runtime import ConstitutionalStateRuntime


class ObserverVerificationResult(BaseModel):
    state_id: str
    state_reconstructed: bool
    state_replayed: bool
    divergence_detected: bool
    remediation_valid: bool
    amendments_valid: bool


class ObserverVerificationEngine:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def verify_state(self, state_id: str) -> ObserverVerificationResult:
        replay_result = self.csr.replay(state_id)
        if isinstance(replay_result, dict):
            diverged = bool(replay_result.get("diverged"))
        else:
            diverged = bool(getattr(replay_result, "diverged", False))
        remediation_valid = not diverged
        amendments_valid = not diverged
        return ObserverVerificationResult(
            state_id=state_id,
            state_reconstructed=True,
            state_replayed=True,
            divergence_detected=diverged,
            remediation_valid=remediation_valid,
            amendments_valid=amendments_valid,
        )
