"""Historical significance tier assignments — drift detection substrate."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime

SIGNIFICANCE_TIER_REGISTER_STATE_ID = "significance_tier_register__global"


class SignificanceTierRecord(BaseModel):
    artifact_id: str
    current_tier: int | None = None
    previous_tier: int | None = None
    rationale: str | None = None
    change_rationale: str | None = None
    pending_reclassification: bool = False
    updated_at: datetime | None = None


class SignificanceTierRegister(BaseModel):
    state_id: str = SIGNIFICANCE_TIER_REGISTER_STATE_ID
    state_type: str = "significance_tier_register"
    records: dict[str, SignificanceTierRecord] = Field(default_factory=dict)

    def record_tier(
        self,
        artifact_id: str,
        tier: int | None,
        *,
        rationale: str | None = None,
        change_rationale: str | None = None,
        now: datetime | None = None,
    ) -> SignificanceTierRecord:
        clock = now or datetime.now(UTC).replace(microsecond=0)
        existing = self.records.get(artifact_id)
        if existing is None:
            record = SignificanceTierRecord(
                artifact_id=artifact_id,
                current_tier=tier,
                rationale=rationale,
                updated_at=clock,
            )
            self.records[artifact_id] = record
            return record

        if existing.current_tier != tier:
            existing.previous_tier = existing.current_tier
            existing.current_tier = tier
            existing.change_rationale = change_rationale
            existing.pending_reclassification = change_rationale is None
        if rationale:
            existing.rationale = rationale
        existing.updated_at = clock
        return existing


def load_significance_tier_register(csr: ConstitutionalStateRuntime) -> SignificanceTierRegister:
    try:
        doc = csr.get_domain_doc(SIGNIFICANCE_TIER_REGISTER_STATE_ID, SignificanceTierRegister)
        assert isinstance(doc, SignificanceTierRegister)
        return doc
    except KeyError:
        return SignificanceTierRegister()


def save_significance_tier_register(
    csr: ConstitutionalStateRuntime,
    register: SignificanceTierRegister,
) -> None:
    csr.register_or_replace_state(
        StateObject(
            state_id=SIGNIFICANCE_TIER_REGISTER_STATE_ID,
            state_type="significance_tier_register",
            current_state="Observed",
        )
    )
    csr.put_domain_doc(SIGNIFICANCE_TIER_REGISTER_STATE_ID, "significance_tier_register", register)


def sync_tier_register_from_index(csr, artifact_index) -> SignificanceTierRegister:
    """Persist current tiers from artifact index for next drift scan."""
    register = load_significance_tier_register(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    for artifact in artifact_index.all():
        register.record_tier(
            artifact.id,
            artifact.significance_tier,
            rationale=artifact.significance_rationale,
            now=now,
        )
    save_significance_tier_register(csr, register)
    return register
