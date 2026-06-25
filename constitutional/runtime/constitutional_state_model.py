"""Constitutional state model — spec-shaped StateObject + aggregator facade.

Aggregates receipts and transition ledger entries into a ``ConstitutionalStateObject``
and emits ``ConstitutionalStateReceiptV2`` via the shared global aggregation pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from constitutional.runtime.global_constitutional_state import (
    GLOBAL_STATE_ID,
    ConstitutionalCondition,
    ConstitutionalStateAggregator,
    GlobalConstitutionalState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.transition_ledger import ConstitutionalTransitionLedger

ConstitutionalStateId = GLOBAL_STATE_ID


class InvariantStress(BaseModel):
    invariant_id: str
    violation_count: int
    recent_triggers: list[str] = Field(default_factory=list)


class RuntimeViolation(BaseModel):
    runtime: str
    violation_count: int
    recent_divergences: list[str] = Field(default_factory=list)


class AmendmentStatus(BaseModel):
    pending: list[str] = Field(default_factory=list)
    ratified: list[str] = Field(default_factory=list)
    deprecated: list[str] = Field(default_factory=list)
    superseded: list[str] = Field(default_factory=list)


class AccountabilityChain(BaseModel):
    chain_id: str
    parties: list[str]
    open_obligations: int


class ObserverChallenge(BaseModel):
    challenge_id: str
    state_object_id: str
    status: Literal["open", "resolved", "escalated"]


class HealthState(BaseModel):
    score: float
    unresolved_divergences: int
    open_remediations: int
    pending_amendments: int
    overdue_obligations: int


class StressState(BaseModel):
    invariants_under_stress: list[InvariantStress]
    runtimes_with_violations: list[RuntimeViolation]


class DebtMetrics(BaseModel):
    """Nested constitutional debt metrics on ``ConstitutionalStateObject``."""

    unresolved_divergences: int
    overdue_remediations: int
    repeated_arbitrations: int
    recurrent_triggers: int
    debt_score: float


class RuntimeCompliance(BaseModel):
    runtime: str
    compliance_score: float
    violations: int
    last_violation_at: Optional[datetime] = None


class SpecCompliance(BaseModel):
    runtime: str
    spec_version: str
    out_of_date: bool
    amendment_required: bool


class ConstitutionalStateObject(BaseModel):
    state_id: str = ConstitutionalStateId
    state_type: str = "constitutional_state"
    snapshot_at: datetime
    version: int
    window: str
    condition: ConstitutionalCondition

    health: HealthState
    stress: StressState
    amendments: AmendmentStatus
    accountability_chains: list[AccountabilityChain]
    observer_challenges_open: int
    observer_challenges: list[ObserverChallenge]
    constitutional_debt: DebtMetrics
    runtime_compliance: list[RuntimeCompliance]
    spec_compliance: list[SpecCompliance]


def _parse_last_violation_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def global_to_constitutional_state_object(
    state: GlobalConstitutionalState,
) -> ConstitutionalStateObject:
    """Map governed ``GlobalConstitutionalState`` to spec-shaped object."""
    return ConstitutionalStateObject(
        state_id=state.state_id,
        state_type=state.state_type,
        snapshot_at=state.snapshot_at,
        version=state.version,
        window=state.window,
        condition=state.condition,
        health=HealthState(
            score=state.health.health_score,
            unresolved_divergences=state.health.unresolved_divergences,
            open_remediations=state.health.open_remediations,
            pending_amendments=state.health.pending_amendments,
            overdue_obligations=state.health.overdue_obligations,
        ),
        stress=StressState(
            invariants_under_stress=[
                InvariantStress(
                    invariant_id=entry.invariant_id,
                    violation_count=entry.violation_count,
                    recent_triggers=list(entry.recent_triggers),
                )
                for entry in state.stress.invariants_under_stress
            ],
            runtimes_with_violations=[
                RuntimeViolation(
                    runtime=entry.runtime,
                    violation_count=entry.violation_count,
                    recent_divergences=list(entry.recent_divergences),
                )
                for entry in state.stress.runtimes_with_violations
            ],
        ),
        amendments=AmendmentStatus(
            pending=list(state.amendments.pending),
            ratified=list(state.amendments.ratified),
            deprecated=list(state.amendments.deprecated),
            superseded=list(state.amendments.superseded),
        ),
        accountability_chains=[
            AccountabilityChain(
                chain_id=chain.chain_id,
                parties=list(chain.parties),
                open_obligations=chain.open_obligations,
            )
            for chain in state.accountability.active_accountability_chains
        ],
        observer_challenges_open=state.accountability.observer_challenges_open,
        observer_challenges=[
            ObserverChallenge(
                challenge_id=challenge.challenge_id,
                state_object_id=challenge.state_object_id,
                status=challenge.status,
            )
            for challenge in state.accountability.observer_challenges
        ],
        constitutional_debt=DebtMetrics(
            unresolved_divergences=state.constitutional_debt.unresolved_divergences,
            overdue_remediations=state.constitutional_debt.overdue_remediations,
            repeated_arbitrations=state.constitutional_debt.repeated_arbitrations,
            recurrent_triggers=state.constitutional_debt.recurrent_triggers,
            debt_score=state.constitutional_debt.debt_score,
        ),
        runtime_compliance=[
            RuntimeCompliance(
                runtime=entry.runtime,
                compliance_score=entry.compliance_score,
                violations=entry.violations,
                last_violation_at=_parse_last_violation_at(entry.last_violation_at),
            )
            for entry in state.compliance.runtime_compliance
        ],
        spec_compliance=[
            SpecCompliance(
                runtime=entry.runtime,
                spec_version=entry.spec_version,
                out_of_date=entry.out_of_date,
                amendment_required=entry.amendment_required,
            )
            for entry in state.compliance.spec_compliance
        ],
    )


class ConstitutionalStateModel:
    """Aggregates receipts + transitions into a ``ConstitutionalStateObject``."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self.ledger: ConstitutionalTransitionLedger = csr.ledger
        from constitutional.runtime import ObserverVerificationEngine

        self.observer = ObserverVerificationEngine(csr)
        self._aggregator = ConstitutionalStateAggregator(csr)

    def update_snapshot(
        self,
        snapshot_at: datetime | None = None,
    ) -> ConstitutionalStateObject:
        now = snapshot_at or datetime.now(UTC)
        global_state = self._aggregator.update_snapshot(snapshot_at=now)
        state_object = global_to_constitutional_state_object(global_state)
        self._verify_constitutional_state_object()
        return state_object

    def _collect_receipts_until(self, now: datetime) -> list:
        return self.csr.get_all_receipts(before=now)

    def _collect_transitions_until(self, now: datetime):
        return [entry for entry in self.ledger.entries if entry.timestamp <= now]

    def _verify_constitutional_state_object(self) -> None:
        try:
            self.observer.verify_state_core(ConstitutionalStateId)
        except KeyError:
            return


def run_constitutional_state_update(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    snapshot_at: datetime | None = None,
) -> ConstitutionalStateObject:
    """Boot-path helper: refresh governed global constitutional state."""
    runtime = csr or ConstitutionalStateRuntime()
    return ConstitutionalStateModel(runtime).update_snapshot(snapshot_at=snapshot_at)
