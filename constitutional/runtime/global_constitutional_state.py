"""Global Constitutional State — governed macro-aggregate (constitutional state spec v0).

Semantically derived from receipts + transition ledger (CS-6).
Constitutionally explicit as StateObject + ConstitutionalStateReceiptV2.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.core.graph import (
    map_domain_state,
    validate_constitutional_condition_transition,
)
from constitutional.core.models import StateObject
from constitutional.runtime.constitutional_debt import compute_constitutional_debt_threats
from constitutional.runtime.governance_gate import all_constitutional_state_ids
from constitutional.runtime.receipt_stream import load_receipts_from_disk, max_receipt_timestamp
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AmendmentReceiptV2,
    ArbitrationReceiptV2,
    AuthorityBlockV2,
    ClosureReceiptV2,
    ConstitutionalStateReceiptV2,
    ConstitutionalStateSnapshotPayloadV2,
    ContinuityBlockV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSourceV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    TransitionReceiptV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass
from constitutional.runtime.runtime import ConstitutionalStateRuntime

GLOBAL_STATE_ID = "constitutional_state__global"
ConstitutionalCondition = Literal["Healthy", "Degraded", "Critical"]
ObserverChallengeStatus = Literal["open", "resolved", "escalated"]

# v0 cumulative window
DEFAULT_WINDOW = "cumulative"

# Health score weights (spec §3)
HEALTH_WEIGHT_DIVERGENCE = 0.2
HEALTH_WEIGHT_REMEDIATION = 0.2
HEALTH_WEIGHT_OVERDUE = 0.3
HEALTH_WEIGHT_AMENDMENT = 0.1
HEALTH_WEIGHT_COMPLIANCE = 0.2

# Normalization caps
DIVERGENCE_NORM_MAX = 10
REMEDIATION_NORM_MAX = 10
OVERDUE_NORM_MAX = 5
AMENDMENT_NORM_MAX = 5
DEBT_NORM_DIVERGENCES = 10
DEBT_NORM_OVERDUE = 5
DEBT_NORM_ARBITRATION = 5
DEBT_NORM_TRIGGERS = 10

REMEDIATION_SLA = timedelta(hours=72)
RECENT_RECEIPT_LIMIT = 5
COMPLIANCE_ALPHA = 0.2

AMENDMENT_PENDING_STAGES = frozenset({"proposed", "evaluated"})
AMENDMENT_RATIFIED_STAGES = frozenset({"ratified", "implemented"})
AMENDMENT_CLOSED_STAGES = frozenset({"observed", "closed"})


class InvariantStressEntry(BaseModel):
    invariant_id: str
    violation_count: int = Field(ge=0)
    recent_triggers: list[str] = Field(default_factory=list)


class RuntimeViolationEntry(BaseModel):
    runtime: str
    violation_count: int = Field(ge=0)
    recent_divergences: list[str] = Field(default_factory=list)


class ConstitutionalHealth(BaseModel):
    """CS-1: score is always computed — never manually assigned."""

    health_score: float = Field(ge=0.0, le=1.0)
    unresolved_divergences: int = Field(ge=0)
    open_remediations: int = Field(ge=0)
    pending_amendments: int = Field(ge=0)
    overdue_obligations: int = Field(ge=0)

    @property
    def score(self) -> float:
        return self.health_score


class ConstitutionalStress(BaseModel):
    invariants_under_stress: list[InvariantStressEntry] = Field(default_factory=list)
    runtimes_with_violations: list[RuntimeViolationEntry] = Field(default_factory=list)


class ConstitutionalAmendmentIndex(BaseModel):
    pending: list[str] = Field(default_factory=list)
    ratified: list[str] = Field(default_factory=list)
    deprecated: list[str] = Field(default_factory=list)
    superseded: list[str] = Field(default_factory=list)


class AccountabilityChainRef(BaseModel):
    chain_id: str
    parties: list[str] = Field(default_factory=list)
    open_obligations: int = Field(default=0, ge=0)


class ObserverChallengeRef(BaseModel):
    challenge_id: str
    state_object_id: str
    status: ObserverChallengeStatus


class ConstitutionalAccountability(BaseModel):
    active_accountability_chains: list[AccountabilityChainRef] = Field(default_factory=list)
    observer_challenges_open: int = Field(ge=0)
    observer_challenges: list[ObserverChallengeRef] = Field(default_factory=list)


class ConstitutionalDebt(BaseModel):
    unresolved_divergences: int = Field(default=0, ge=0)
    overdue_remediations: int = Field(default=0, ge=0)
    repeated_arbitrations: int = Field(default=0, ge=0)
    recurrent_triggers: int = Field(default=0, ge=0)
    debt_score: float = Field(default=0.0, ge=0.0, le=1.0)
    threats: list[ReconstructabilityFailureClass] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return (
            self.unresolved_divergences
            + self.overdue_remediations
            + self.repeated_arbitrations
            + self.recurrent_triggers
        )


class RuntimeComplianceEntry(BaseModel):
    runtime: str
    compliance_score: float = Field(ge=0.0, le=1.0)
    violations: int = Field(ge=0)
    last_violation_at: str | None = None


class SpecComplianceEntry(BaseModel):
    runtime: str
    spec_version: str
    out_of_date: bool = False
    amendment_required: bool = False


class ConstitutionalCompliance(BaseModel):
    runtime_compliance: list[RuntimeComplianceEntry] = Field(default_factory=list)
    spec_compliance: list[SpecComplianceEntry] = Field(default_factory=list)


class GlobalConstitutionalState(BaseModel):
    state_id: str = GLOBAL_STATE_ID
    state_type: str = "constitutional_state"
    snapshot_at: datetime
    version: int = Field(ge=1)
    window: str = DEFAULT_WINDOW
    condition: ConstitutionalCondition

    health: ConstitutionalHealth
    stress: ConstitutionalStress
    amendments: ConstitutionalAmendmentIndex
    accountability: ConstitutionalAccountability
    constitutional_debt: ConstitutionalDebt
    compliance: ConstitutionalCompliance = Field(default_factory=ConstitutionalCompliance)


class ConstitutionalStateInvariantError(ValueError):
    """Raised when CS-1..CS-6 invariants are violated."""


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize(count: int, cap: int) -> float:
    if cap <= 0:
        return 0.0
    return _clamp01(count / cap)


def compute_constitutional_debt_score(
    *,
    unresolved_divergences: int,
    overdue_remediations: int,
    repeated_arbitrations: int,
    recurrent_triggers: int,
) -> float:
    """CS-2: debt_score from normalized obligation components (spec §Step 4)."""
    du = _normalize(unresolved_divergences, DEBT_NORM_DIVERGENCES)
    ro = _normalize(overdue_remediations, DEBT_NORM_OVERDUE)
    ar = _normalize(repeated_arbitrations, DEBT_NORM_ARBITRATION)
    tr = _normalize(recurrent_triggers, DEBT_NORM_TRIGGERS)
    return _clamp01((du + ro + ar + tr) / 4.0)


def compute_health_score(
    *,
    unresolved_divergences: int,
    open_remediations: int,
    overdue_obligations: int,
    pending_amendments: int,
    average_compliance_deficit: float,
) -> float:
    """CS-1: deterministic health from counts (spec §Step 3)."""
    d = _normalize(unresolved_divergences, DIVERGENCE_NORM_MAX)
    r = _normalize(open_remediations, REMEDIATION_NORM_MAX)
    o = _normalize(overdue_obligations, OVERDUE_NORM_MAX)
    a = _normalize(pending_amendments, AMENDMENT_NORM_MAX)
    c = _clamp01(average_compliance_deficit)
    score = (
        1.0
        - HEALTH_WEIGHT_DIVERGENCE * d
        - HEALTH_WEIGHT_REMEDIATION * r
        - HEALTH_WEIGHT_OVERDUE * o
        - HEALTH_WEIGHT_AMENDMENT * a
        - HEALTH_WEIGHT_COMPLIANCE * c
    )
    return _clamp01(score)


def condition_from_health_score(score: float) -> ConstitutionalCondition:
    if score >= 0.8:
        return "Healthy"
    if score >= 0.5:
        return "Degraded"
    return "Critical"


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _collect_csr_transition_receipts(
    csr: ConstitutionalStateRuntime,
    *,
    up_to: datetime,
) -> list[TransitionReceiptV2]:
    receipts: list[TransitionReceiptV2] = []
    with csr._lock:  # noqa: SLF001
        for bucket in csr._receipts_by_state.values():
            for receipt in bucket:
                if _parse_ts(receipt.timestamp) <= up_to:
                    receipts.append(receipt)
    return receipts


def _collect_csr_domain_receipts(csr: ConstitutionalStateRuntime, *, up_to: datetime) -> list:
    receipts: list = []
    with csr._lock:  # noqa: SLF001
        for bucket in csr._domain_receipts_by_state.values():
            for receipt in bucket:
                if _parse_ts(receipt.timestamp) <= up_to:
                    receipts.append(receipt)
    return receipts


def _state_id_for_receipt(receipt) -> str:
    if hasattr(receipt, "transition") and receipt.transition.state_id:
        return receipt.transition.state_id
    return receipt.inputs.request_id


def _merge_receipt_streams(
    csr: ConstitutionalStateRuntime,
    *,
    snapshot_at: datetime,
) -> list:
    """R ∪ CSR streams — cumulative window (spec §Step 1)."""
    disk = load_receipts_from_disk(up_to=snapshot_at)
    in_memory = _collect_csr_transition_receipts(csr, up_to=snapshot_at)
    domain = _collect_csr_domain_receipts(csr, up_to=snapshot_at)
    by_id: dict[str, object] = {}
    for receipt in [*disk, *in_memory, *domain]:
        by_id[getattr(receipt, "receipt_id", id(receipt))] = receipt
    return list(by_id.values())


def _count_replay_divergences(csr: ConstitutionalStateRuntime) -> tuple[int, list[str]]:
    count = 0
    ids: list[str] = []
    for state_id in all_constitutional_state_ids(csr):
        if state_id == GLOBAL_STATE_ID:
            continue
        try:
            replay = csr.replay(state_id)
            if replay.diverged:
                count += 1
                ids.append(state_id)
        except KeyError:
            continue
    return count, ids


def _count_unresolved_from_receipts(
    receipts: list,
    *,
    replay_divergence_ids: list[str],
) -> int:
    divergences_by_state: dict[str, list[str]] = {}
    remediated_states: set[str] = set()
    closed_states: set[str] = set()

    for receipt in receipts:
        state_id = _state_id_for_receipt(receipt)
        if isinstance(receipt, DivergenceReceiptV2):
            divergences_by_state.setdefault(state_id, []).append(receipt.receipt_id)
        elif isinstance(receipt, RemediationReceiptV2):
            remediated_states.add(state_id)
        elif isinstance(receipt, ClosureReceiptV2):
            closed_states.add(state_id)

    unresolved = 0
    for state_id, _div_ids in divergences_by_state.items():
        if state_id not in remediated_states and state_id not in closed_states:
            unresolved += 1
    unresolved += len(
        [sid for sid in replay_divergence_ids if sid not in remediated_states and sid not in closed_states]
    )
    return unresolved


def _scan_remediations(
    receipts: list,
    *,
    snapshot_at: datetime,
) -> tuple[int, int]:
    open_count = 0
    overdue_count = 0
    open_by_state: dict[str, RemediationReceiptV2] = {}
    closed_states: set[str] = set()

    for receipt in receipts:
        if isinstance(receipt, ClosureReceiptV2):
            closed_states.add(_state_id_for_receipt(receipt))
        if isinstance(receipt, RemediationReceiptV2):
            open_by_state[_state_id_for_receipt(receipt)] = receipt

    for state_id, remediation in open_by_state.items():
        if state_id in closed_states:
            continue
        open_count += 1
        ts = _parse_ts(remediation.timestamp)
        deadline = remediation.remediation.deadline
        if deadline:
            try:
                due = _parse_ts(deadline)
                if snapshot_at > due:
                    overdue_count += 1
            except ValueError:
                overdue_count += 1
        elif snapshot_at - ts > REMEDIATION_SLA:
            overdue_count += 1
    return open_count, overdue_count


def _index_amendments(receipts: list) -> ConstitutionalAmendmentIndex:
    by_amendment: dict[str, AmendmentReceiptV2] = {}
    for receipt in receipts:
        if isinstance(receipt, AmendmentReceiptV2):
            key = receipt.amendment.article + ":" + receipt.amendment.amendment_stage
            by_amendment[receipt.receipt_id] = receipt

    pending: list[str] = []
    ratified: list[str] = []
    deprecated: list[str] = []
    superseded: list[str] = []

    for receipt_id, receipt in by_amendment.items():
        stage = receipt.amendment.amendment_stage
        if stage in AMENDMENT_PENDING_STAGES:
            pending.append(receipt_id)
        elif stage in AMENDMENT_RATIFIED_STAGES or stage in AMENDMENT_CLOSED_STAGES:
            ratified.append(receipt_id)
        if receipt.amendment.change_type == "removal":
            deprecated.append(receipt_id)

    return ConstitutionalAmendmentIndex(
        pending=sorted(pending),
        ratified=sorted(ratified),
        deprecated=sorted(deprecated),
        superseded=sorted(superseded),
    )


def _scan_stress(receipts: list) -> ConstitutionalStress:
    invariant_triggers: dict[str, list[str]] = {}
    invariant_counts: dict[str, int] = {}
    runtime_divs: dict[str, list[str]] = {}
    runtime_counts: dict[str, int] = {}

    failure_stages = {"divergence", "remediation"}

    for receipt in receipts:
        inv = getattr(receipt, "invariant", None)
        inv_name = getattr(inv, "name", None) if inv else None
        inv_ok = getattr(inv, "satisfied", True) if inv else True
        stage = getattr(getattr(receipt, "lifecycle", None), "stage", None)
        is_failure = (
            isinstance(receipt, (DivergenceReceiptV2, RemediationReceiptV2, ArbitrationReceiptV2))
            or stage in failure_stages
            or not inv_ok
        )
        if not is_failure:
            continue
        if inv_name:
            invariant_counts[inv_name] = invariant_counts.get(inv_name, 0) + 1
            triggers = invariant_triggers.setdefault(inv_name, [])
            if len(triggers) < RECENT_RECEIPT_LIMIT:
                triggers.append(receipt.receipt_id)
        if isinstance(receipt, DivergenceReceiptV2):
            runtime_counts[receipt.runtime] = runtime_counts.get(receipt.runtime, 0) + 1
            recent = runtime_divs.setdefault(receipt.runtime, [])
            if len(recent) < RECENT_RECEIPT_LIMIT:
                recent.append(receipt.receipt_id)

    return ConstitutionalStress(
        invariants_under_stress=[
            InvariantStressEntry(
                invariant_id=k,
                violation_count=v,
                recent_triggers=invariant_triggers.get(k, []),
            )
            for k, v in sorted(invariant_counts.items())
        ],
        runtimes_with_violations=[
            RuntimeViolationEntry(
                runtime=k,
                violation_count=v,
                recent_divergences=runtime_divs.get(k, []),
            )
            for k, v in sorted(runtime_counts.items())
        ],
    )


def _recurrent_invariant_triggers(receipts: list) -> int:
    counts: dict[str, int] = {}
    for receipt in receipts:
        if isinstance(receipt, RemediationReceiptV2) and receipt.remediation.constitutional_trigger:
            inv = receipt.invariant.name
            counts[inv] = counts.get(inv, 0) + 1
    return sum(1 for c in counts.values() if c > 1)


def _accountability_from_csr(
    csr: ConstitutionalStateRuntime,
    receipts: list,
) -> ConstitutionalAccountability:
    chains: list[AccountabilityChainRef] = []
    challenges: list[ObserverChallengeRef] = []
    open_challenges = 0

    closed_states: set[str] = {
        _state_id_for_receipt(r) for r in receipts if isinstance(r, ClosureReceiptV2)
    }

    for state in csr._states.values():  # noqa: SLF001
        if state.state_id == GLOBAL_STATE_ID:
            continue
        if state.accountability_chain:
            open_obligations = 1 if state.current_state in {"Challenged", "Arbitrated", "Remediated"} else 0
            chains.append(
                AccountabilityChainRef(
                    chain_id=state.state_id,
                    parties=list(state.accountability_chain),
                    open_obligations=open_obligations,
                )
            )
        if state.current_state == "Challenged":
            status: ObserverChallengeStatus = "open"
            open_challenges += 1
        elif state.current_state == "Arbitrated":
            status = "escalated"
            open_challenges += 1
        elif state.current_state == "Remediated" and state.state_id not in closed_states:
            status = "open"
            open_challenges += 1
        else:
            continue
        challenges.append(
            ObserverChallengeRef(
                challenge_id=f"challenge-{state.state_id}",
                state_object_id=state.state_id,
                status=status,
            )
        )

    for receipt in receipts:
        if isinstance(receipt, DivergenceReceiptV2):
            sid = _state_id_for_receipt(receipt)
            if sid not in {c.state_object_id for c in challenges}:
                challenges.append(
                    ObserverChallengeRef(
                        challenge_id=receipt.receipt_id,
                        state_object_id=sid,
                        status="open" if sid not in closed_states else "resolved",
                    )
                )
                if sid not in closed_states:
                    open_challenges += 1

    return ConstitutionalAccountability(
        active_accountability_chains=chains,
        observer_challenges_open=open_challenges,
        observer_challenges=challenges,
    )


def _compliance_from_receipts(
    receipts: list,
    *,
    unresolved_by_runtime: dict[str, int],
) -> ConstitutionalCompliance:
    violations: dict[str, int] = {}
    last_violation: dict[str, str] = {}
    runtimes_seen: set[str] = set()

    for receipt in receipts:
        runtimes_seen.add(receipt.runtime)
        if isinstance(receipt, (DivergenceReceiptV2, RemediationReceiptV2, ArbitrationReceiptV2)):
            violations[receipt.runtime] = violations.get(receipt.runtime, 0) + 1
            last_violation[receipt.runtime] = receipt.timestamp

    runtime_compliance: list[RuntimeComplianceEntry] = []
    for runtime in sorted(runtimes_seen):
        v = violations.get(runtime, 0) + unresolved_by_runtime.get(runtime, 0)
        score = 1.0 / (1.0 + COMPLIANCE_ALPHA * v) if v > 0 else 1.0
        if unresolved_by_runtime.get(runtime, 0) > 0:
            score = min(score, 0.99)
        runtime_compliance.append(
            RuntimeComplianceEntry(
                runtime=runtime,
                compliance_score=_clamp01(score),
                violations=v,
                last_violation_at=last_violation.get(runtime),
            )
        )

    spec_entries = [
        SpecComplianceEntry(
            runtime=runtime,
            spec_version="v0",
            out_of_date=False,
            amendment_required=False,
        )
        for runtime in sorted(runtimes_seen)
    ]

    return ConstitutionalCompliance(
        runtime_compliance=runtime_compliance,
        spec_compliance=spec_entries,
    )


def validate_constitutional_state_invariants(
    state: GlobalConstitutionalState,
    *,
    previous: GlobalConstitutionalState | None,
    receipts: list,
    recomputed_health: float,
    recomputed_debt: float,
) -> None:
    """Enforce CS-1..CS-6 on a snapshot."""
    if abs(state.health.health_score - recomputed_health) > 1e-9:
        raise ConstitutionalStateInvariantError("CS-1: health_score is not deterministic")
    if abs(state.constitutional_debt.debt_score - recomputed_debt) > 1e-9:
        raise ConstitutionalStateInvariantError("CS-1: debt_score is not deterministic")

    if previous is not None:
        obligations_closed = (
            state.constitutional_debt.unresolved_divergences < previous.constitutional_debt.unresolved_divergences
            or state.constitutional_debt.overdue_remediations < previous.constitutional_debt.overdue_remediations
        )
        debt_increased = state.constitutional_debt.debt_score > previous.constitutional_debt.debt_score + 1e-9
        if obligations_closed and debt_increased:
            raise ConstitutionalStateInvariantError(
                "CS-2: debt_score increased while obligations were closed"
            )

    for entry in state.compliance.runtime_compliance:
        if entry.violations > 0 and entry.compliance_score >= 1.0:
            raise ConstitutionalStateInvariantError(
                f"CS-4: runtime {entry.runtime} has violations but compliance_score == 1.0"
            )

    max_ts = max_receipt_timestamp([r for r in receipts if hasattr(r, "timestamp")])
    if max_ts is not None and state.snapshot_at < max_ts.replace(microsecond=0):
        raise ConstitutionalStateInvariantError("CS-5: snapshot_at precedes included receipt timestamps")


def aggregate_global_constitutional_state(
    csr: ConstitutionalStateRuntime,
    *,
    snapshot_at: datetime | None = None,
    previous: GlobalConstitutionalState | None = None,
    window: str = DEFAULT_WINDOW,
) -> GlobalConstitutionalState:
    """Derive governed global constitutional state from ledger + receipt stream (spec §Steps 1–5)."""
    now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
    receipts = _merge_receipt_streams(csr, snapshot_at=now)

    max_ts = max_receipt_timestamp([r for r in receipts if hasattr(r, "timestamp")])
    if max_ts is not None and now < max_ts.replace(microsecond=0):
        now = max_ts.replace(microsecond=0)

    replay_count, replay_ids = _count_replay_divergences(csr)
    unresolved = max(
        _count_unresolved_from_receipts(receipts, replay_divergence_ids=replay_ids),
        replay_count,
    )
    open_remediations, overdue_remediations = _scan_remediations(receipts, snapshot_at=now)
    amendments = _index_amendments(receipts)
    stress = _scan_stress(receipts)
    accountability = _accountability_from_csr(csr, receipts)

    repeated_arbitrations = sum(
        1 for s in csr._states.values() if s.current_state in {"Challenged", "Arbitrated"}  # noqa: SLF001
    )
    recurrent_triggers = _recurrent_invariant_triggers(receipts)

    debt_score = compute_constitutional_debt_score(
        unresolved_divergences=unresolved,
        overdue_remediations=overdue_remediations,
        repeated_arbitrations=repeated_arbitrations,
        recurrent_triggers=recurrent_triggers,
    )
    threats = compute_constitutional_debt_threats(
        unresolved_divergences=unresolved,
        overdue_remediations=overdue_remediations,
        replay_diverged=unresolved > 0,
        closed_without_receipts=repeated_arbitrations,
        unobserved_amendments=len(amendments.pending),
    )

    unresolved_by_runtime = {e.runtime: e.violation_count for e in stress.runtimes_with_violations}
    compliance = _compliance_from_receipts(receipts, unresolved_by_runtime=unresolved_by_runtime)
    avg_compliance_deficit = 0.0
    if compliance.runtime_compliance:
        avg_compliance_deficit = sum(
            1.0 - e.compliance_score for e in compliance.runtime_compliance
        ) / len(compliance.runtime_compliance)

    health_score = compute_health_score(
        unresolved_divergences=unresolved,
        open_remediations=open_remediations,
        overdue_obligations=overdue_remediations,
        pending_amendments=len(amendments.pending),
        average_compliance_deficit=avg_compliance_deficit,
    )
    condition = condition_from_health_score(health_score)
    version = (previous.version + 1) if previous else 1

    state = GlobalConstitutionalState(
        snapshot_at=now,
        version=version,
        window=window,
        condition=condition,
        health=ConstitutionalHealth(
            health_score=health_score,
            unresolved_divergences=unresolved,
            open_remediations=open_remediations,
            pending_amendments=len(amendments.pending),
            overdue_obligations=overdue_remediations,
        ),
        stress=stress,
        amendments=amendments,
        accountability=accountability,
        constitutional_debt=ConstitutionalDebt(
            unresolved_divergences=unresolved,
            overdue_remediations=overdue_remediations,
            repeated_arbitrations=repeated_arbitrations,
            recurrent_triggers=recurrent_triggers,
            debt_score=debt_score,
            threats=threats,
        ),
        compliance=compliance,
    )

    validate_constitutional_state_invariants(
        state,
        previous=previous,
        receipts=receipts,
        recomputed_health=health_score,
        recomputed_debt=debt_score,
    )
    return state


def build_constitutional_state_receipt(
    state: GlobalConstitutionalState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
    evidence_ids: list[str] | None = None,
) -> ConstitutionalStateReceiptV2:
    snapshot_payload = ConstitutionalStateSnapshotPayloadV2(
        health_score=state.health.health_score,
        debt_score=state.constitutional_debt.debt_score,
        constitutional_debt=state.constitutional_debt.total,
        unresolved_divergences=state.health.unresolved_divergences,
        open_remediations=state.health.open_remediations,
        pending_amendments=state.health.pending_amendments,
        overdue_obligations=state.health.overdue_obligations,
        condition=state.condition,
        version=state.version,
        window=state.window,
    )
    payload_hash = stable_json_hash(
        {
            **snapshot_payload.model_dump(),
            "threats": [t.value for t in state.constitutional_debt.threats],
        }
    )
    receipt_id = new_receipt_id("csr")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    evidence_bundle = evidence_ids or ["ledger", "receipt-stream"]
    return ConstitutionalStateReceiptV2(
        receipt_id=receipt_id,
        runtime="ConstitutionalStateRuntime",
        timestamp=ts,
        action_type="constitutional_state_snapshot",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="observed",
            result_hash=payload_hash,
            notes=f"Global constitutional state v{state.version} condition={state.condition}",
        ),
        invariant=InvariantBlockV2(
            name="SYSTEM_MUST_TRACK_ITS_OWN_CONSTITUTIONAL_HEALTH",
            description="Constitutional state is receipted and reproducible from ledger + receipts",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"constitutional-state-evidence-{state.version}",
            sources=[
                EvidenceSourceV2(id=eid, type="ledger", provenance="csr")
                for eid in evidence_bundle
            ],
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="ConstitutionalStateRuntime",
            jurisdiction="governance",
            legitimacy_basis="Article XVI",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance_only"],
            scope_out=["execution"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="ConstitutionalSteward"),
        signatures=SignaturesBlockV2(runtime_signature="sig-csr-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected="closure",
        ),
        observation=ObservationPayloadV2(
            observed_status=state.condition,
            observed_at=ts,
            observer_jurisdiction="constitutional",
            notes=(
                f"debt_score={state.constitutional_debt.debt_score:.2f} "
                f"health={state.health.health_score:.2f} window={state.window}"
            ),
        ),
        constitutional_state=snapshot_payload,
        threats=list(state.constitutional_debt.threats),
    )


def _ensure_state_object(csr: ConstitutionalStateRuntime, condition: ConstitutionalCondition) -> StateObject:
    universal = map_domain_state("constitutional_state", condition)
    try:
        return csr.get_state(GLOBAL_STATE_ID)
    except KeyError:
        state = StateObject(
            state_id=GLOBAL_STATE_ID,
            state_type="constitutional_state",
            current_state=universal,
            invariants=["SYSTEM_MUST_TRACK_ITS_OWN_CONSTITUTIONAL_HEALTH"],
            accountability_chain=["ConstitutionalSteward"],
        )
        csr.register_state(state)
        return state


def _sync_state_object_mirror(
    csr: ConstitutionalStateRuntime,
    condition: ConstitutionalCondition,
) -> None:
    universal = map_domain_state("constitutional_state", condition)
    try:
        existing = csr.get_state(GLOBAL_STATE_ID)
        if existing.current_state == universal:
            return
    except KeyError:
        _ensure_state_object(csr, condition)
        return
    with csr._lock:  # noqa: SLF001
        csr._states[GLOBAL_STATE_ID] = existing.model_copy(
            update={"current_state": universal, "version": existing.version + 1}
        )


class ConstitutionalStateAggregator:
    """Aggregator over ledger + receipts — not a separate execution runtime."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None
        self._last_condition: ConstitutionalCondition | None = None

    def update_snapshot(
        self,
        snapshot_at: datetime | None = None,
        *,
        window: str = DEFAULT_WINDOW,
    ) -> GlobalConstitutionalState:
        try:
            previous = self.csr.get_global_snapshot()
            assert isinstance(previous, GlobalConstitutionalState)
        except KeyError:
            previous = None

        state = aggregate_global_constitutional_state(
            self.csr,
            snapshot_at=snapshot_at,
            previous=previous,
            window=window,
        )

        _ensure_state_object(self.csr, state.condition)
        prior_condition = self._last_condition or (
            previous.condition if previous else state.condition
        )
        if prior_condition != state.condition:
            validate_constitutional_condition_transition(prior_condition, state.condition)

        _sync_state_object_mirror(self.csr, state.condition)
        self.csr.register_global_snapshot(state)
        receipt = build_constitutional_state_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash
        self._last_condition = state.condition
        return state
