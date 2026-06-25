"""Constitutional Risk Runtime — governed forecaster over receipts + constitutional state.

Never mutates governed state directly. Emits RiskReceiptV2 observations that Amendment,
Institutional, and Operator runtimes may treat as early warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.runtime.global_constitutional_state import (
    GLOBAL_STATE_ID,
    GlobalConstitutionalState,
)
from constitutional.runtime.receipt_stream import _parse_timestamp
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    ArbitrationReceiptV2,
    AuthorityBlockV2,
    ConstitutionalRiskPayloadV2,
    ConstitutionalStateReceiptV2,
    ContinuityBlockV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    PredictedFailureV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    RecommendedActionV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    RiskFactorV2,
    RiskReceiptV2,
    RiskScopeV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

RISK_RUNTIME_NAME = "ConstitutionalRiskRuntime"
RISK_INVARIANT = "SYSTEM_MUST_FORECAST_CONSTITUTIONAL_FAILURES_FROM_EVIDENCE"
DEFAULT_HORIZON = "7d"
DEFAULT_LOOKBACK = timedelta(days=30)
REMEDIATION_SLA = timedelta(days=7)

# Normalization caps (v0 deterministic scoring)
DIVERGENCE_CAP = 10
OVERDUE_CAP = 5
ARBITRATION_CAP = 5

# Weights — overdue obligations and downward health trend dominate
WEIGHT_DIVERGENCE = 0.2
WEIGHT_OVERDUE = 0.4
WEIGHT_ARBITRATION = 0.15
WEIGHT_HEALTH_SLOPE = 0.25

PredictionType = Literal[
    "remediation_failure",
    "amendment_required",
    "governance_breakdown",
]


class ConstitutionalRiskScope(BaseModel):
    runtime: str
    invariant: str
    tenant: str | None = None


class RiskFactor(BaseModel):
    factor: str
    weight: float
    value: float


class PredictedFailure(BaseModel):
    type: PredictionType
    invariant: str
    probability: float
    horizon: str = DEFAULT_HORIZON


class RecommendedAction(BaseModel):
    type: Literal[
        "initiate_amendment_analysis",
        "escalate_remediation",
        "increase_observer_scrutiny",
        "acknowledge_or_dismiss",
    ]
    target: str
    urgency: Literal["low", "medium", "high", "critical"]


class ConstitutionalRiskState(BaseModel):
    """Forecast StateObject — observation only, not a legal transition target."""

    state_id: str
    state_type: str = "constitutional_risk"
    scope: ConstitutionalRiskScope
    snapshot_at: datetime
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    predicted_failures: list[PredictedFailure] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)


@dataclass(frozen=True)
class _ScopeMetrics:
    divergences: int
    remediations: int
    overdue_remediations: int
    arbitrations: int
    health_slope: float
    divergences_increasing: bool


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower() or "unknown"


def _risk_state_id(scope: ConstitutionalRiskScope, snapshot_at: datetime) -> str:
    ts = snapshot_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"risk__{_slug(scope.runtime)}__{_slug(scope.invariant)}__{ts}"


def _receipt_in_window(receipt, *, start: datetime, end: datetime) -> bool:
    ts = _parse_timestamp(getattr(receipt, "timestamp", ""))
    return start <= ts <= end


def _matches_scope(
    receipt,
    *,
    runtime: str,
    invariant: str,
) -> bool:
    inv = getattr(getattr(receipt, "invariant", None), "name", None)
    if runtime != "__global__" and receipt.runtime != runtime:
        return False
    if invariant != "__global__" and inv and inv != invariant:
        return False
    return True


def _health_slope_from_snapshots(
    receipts: list,
    *,
    start: datetime,
    end: datetime,
) -> float:
    points: list[tuple[datetime, float]] = []
    for receipt in receipts:
        if not isinstance(receipt, ConstitutionalStateReceiptV2):
            continue
        if not _receipt_in_window(receipt, start=start, end=end):
            continue
        ts = _parse_timestamp(receipt.timestamp)
        points.append((ts, receipt.constitutional_state.health_score))
    if len(points) < 2:
        return 0.0
    points.sort(key=lambda p: p[0])
    first_ts, first_score = points[0]
    last_ts, last_score = points[-1]
    days = max((last_ts - first_ts).total_seconds() / 86400.0, 1.0 / 24.0)
    return (last_score - first_score) / days


def _count_overdue_remediations(
    receipts: list,
    *,
    start: datetime,
    end: datetime,
    now: datetime,
    runtime: str,
    invariant: str,
) -> int:
    remediations = [
        r
        for r in receipts
        if isinstance(r, RemediationReceiptV2)
        and _receipt_in_window(r, start=start, end=end)
        and _matches_scope(r, runtime=runtime, invariant=invariant)
    ]
    closed_objects = {
        getattr(getattr(r, "inputs", None), "request_id", "")
        for r in receipts
        if getattr(getattr(r, "lifecycle", None), "stage", None) == "closure"
    }
    overdue = 0
    for rem in remediations:
        obj_id = rem.inputs.request_id
        if obj_id in closed_objects:
            continue
        rem_ts = _parse_timestamp(rem.timestamp)
        if now - rem_ts > REMEDIATION_SLA:
            overdue += 1
    return overdue


def _divergences_increasing(
    receipts: list,
    *,
    start: datetime,
    end: datetime,
    runtime: str,
    invariant: str,
) -> bool:
    divs = [
        _parse_timestamp(r.timestamp)
        for r in receipts
        if isinstance(r, DivergenceReceiptV2)
        and _receipt_in_window(r, start=start, end=end)
        and _matches_scope(r, runtime=runtime, invariant=invariant)
    ]
    if len(divs) < 2:
        return False
    divs.sort()
    mid = len(divs) // 2
    return len(divs[mid:]) > len(divs[:mid])


def _scope_metrics(
    receipts: list,
    *,
    runtime: str,
    invariant: str,
    start: datetime,
    end: datetime,
    now: datetime,
) -> _ScopeMetrics:
    divergences = sum(
        1
        for r in receipts
        if isinstance(r, DivergenceReceiptV2)
        and _receipt_in_window(r, start=start, end=end)
        and _matches_scope(r, runtime=runtime, invariant=invariant)
    )
    remediations = sum(
        1
        for r in receipts
        if isinstance(r, RemediationReceiptV2)
        and _receipt_in_window(r, start=start, end=end)
        and _matches_scope(r, runtime=runtime, invariant=invariant)
    )
    arbitrations = sum(
        1
        for r in receipts
        if isinstance(r, ArbitrationReceiptV2)
        and _receipt_in_window(r, start=start, end=end)
        and _matches_scope(r, runtime=runtime, invariant=invariant)
    )
    overdue = _count_overdue_remediations(
        receipts,
        start=start,
        end=end,
        now=now,
        runtime=runtime,
        invariant=invariant,
    )
    health_slope = _health_slope_from_snapshots(receipts, start=start, end=end)
    return _ScopeMetrics(
        divergences=divergences,
        remediations=remediations,
        overdue_remediations=overdue,
        arbitrations=arbitrations,
        health_slope=health_slope,
        divergences_increasing=_divergences_increasing(
            receipts,
            start=start,
            end=end,
            runtime=runtime,
            invariant=invariant,
        ),
    )


def compute_scope_risk_score(metrics: _ScopeMetrics) -> tuple[float, list[RiskFactor]]:
    d = _clamp01(metrics.divergences / DIVERGENCE_CAP)
    o = _clamp01(metrics.overdue_remediations / OVERDUE_CAP)
    a = _clamp01(metrics.arbitrations / ARBITRATION_CAP)
    h = _clamp01(max(0.0, -metrics.health_slope))

    score = (
        WEIGHT_DIVERGENCE * d
        + WEIGHT_OVERDUE * o
        + WEIGHT_ARBITRATION * a
        + WEIGHT_HEALTH_SLOPE * h
    )
    factors = [
        RiskFactor(factor="unresolved_divergences", weight=WEIGHT_DIVERGENCE, value=metrics.divergences),
        RiskFactor(factor="overdue_remediations", weight=WEIGHT_OVERDUE, value=metrics.overdue_remediations),
        RiskFactor(factor="arbitrations", weight=WEIGHT_ARBITRATION, value=metrics.arbitrations),
        RiskFactor(factor="health_score_decline", weight=WEIGHT_HEALTH_SLOPE, value=h),
    ]
    if metrics.remediations:
        factors.append(
            RiskFactor(factor="open_remediations", weight=0.0, value=float(metrics.remediations))
        )
    return _clamp01(score), factors


def _probability_from_risk(risk_score: float) -> float:
    return _clamp01(0.1 + 0.85 * risk_score)


def predict_failures(
    *,
    risk_score: float,
    metrics: _ScopeMetrics,
    invariant: str,
    horizon: str = DEFAULT_HORIZON,
) -> list[PredictedFailure]:
    predictions: list[PredictedFailure] = []
    prob = _probability_from_risk(risk_score)

    if risk_score > 0.7 and metrics.overdue_remediations > 0:
        predictions.append(
            PredictedFailure(
                type="remediation_failure",
                invariant=invariant,
                probability=prob,
                horizon=horizon,
            )
        )
    if risk_score > 0.8 and metrics.divergences_increasing:
        predictions.append(
            PredictedFailure(
                type="amendment_required",
                invariant=invariant,
                probability=prob,
                horizon=horizon,
            )
        )
    if risk_score > 0.9 and metrics.arbitrations >= 2:
        predictions.append(
            PredictedFailure(
                type="governance_breakdown",
                invariant=invariant,
                probability=prob,
                horizon=horizon,
            )
        )
    return predictions


def recommend_actions(
    *,
    scope: ConstitutionalRiskScope,
    risk_score: float,
    predictions: list[PredictedFailure],
) -> list[RecommendedAction]:
    actions: list[RecommendedAction] = []
    target = scope.runtime if scope.runtime != "__global__" else "constitutional_system"

    for prediction in predictions:
        if prediction.type == "amendment_required":
            actions.append(
                RecommendedAction(
                    type="initiate_amendment_analysis",
                    target=target,
                    urgency="high" if risk_score > 0.85 else "medium",
                )
            )
        elif prediction.type == "remediation_failure":
            actions.append(
                RecommendedAction(
                    type="escalate_remediation",
                    target=target,
                    urgency="critical" if risk_score > 0.85 else "high",
                )
            )
        elif prediction.type == "governance_breakdown":
            actions.append(
                RecommendedAction(
                    type="increase_observer_scrutiny",
                    target=target,
                    urgency="critical",
                )
            )

    if risk_score > 0.6 and not actions:
        actions.append(
            RecommendedAction(
                type="acknowledge_or_dismiss",
                target=target,
                urgency="medium" if risk_score < 0.8 else "high",
            )
        )
    return actions


def discover_risk_scopes(
    receipts: list,
    global_state: GlobalConstitutionalState | None,
) -> list[ConstitutionalRiskScope]:
    scopes: dict[tuple[str, str], ConstitutionalRiskScope] = {}

    for receipt in receipts:
        if isinstance(receipt, (DivergenceReceiptV2, RemediationReceiptV2, ArbitrationReceiptV2)):
            inv = getattr(getattr(receipt, "invariant", None), "name", None) or "__global__"
            key = (receipt.runtime, inv)
            scopes[key] = ConstitutionalRiskScope(runtime=receipt.runtime, invariant=inv)

    if global_state is not None:
        for entry in global_state.stress.invariants_under_stress:
            for rt_entry in global_state.stress.runtimes_with_violations:
                key = (rt_entry.runtime, entry.invariant_id)
                scopes[key] = ConstitutionalRiskScope(
                    runtime=rt_entry.runtime,
                    invariant=entry.invariant_id,
                )
        scopes[("__global__", "__global__")] = ConstitutionalRiskScope(
            runtime="__global__",
            invariant="__global__",
        )

    if not scopes:
        scopes[("__global__", "__global__")] = ConstitutionalRiskScope(
            runtime="__global__",
            invariant="__global__",
        )
    return list(scopes.values())


def build_risk_state(
    *,
    scope: ConstitutionalRiskScope,
    snapshot_at: datetime,
    metrics: _ScopeMetrics,
) -> ConstitutionalRiskState:
    risk_score, factors = compute_scope_risk_score(metrics)
    predictions = predict_failures(
        risk_score=risk_score,
        metrics=metrics,
        invariant=scope.invariant,
    )
    actions = recommend_actions(scope=scope, risk_score=risk_score, predictions=predictions)
    return ConstitutionalRiskState(
        state_id=_risk_state_id(scope, snapshot_at),
        scope=scope,
        snapshot_at=snapshot_at,
        risk_score=risk_score,
        risk_factors=factors,
        predicted_failures=predictions,
        recommended_actions=actions,
    )


def build_risk_receipt(
    state: ConstitutionalRiskState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
    lookback_days: int = 30,
) -> RiskReceiptV2:
    payload = ConstitutionalRiskPayloadV2(
        risk_score=state.risk_score,
        scope=RiskScopeV2(
            runtime=state.scope.runtime,
            invariant=state.scope.invariant,
            tenant=state.scope.tenant,
        ),
        risk_factors=[
            RiskFactorV2(factor=f.factor, weight=f.weight, value=f.value)
            for f in state.risk_factors
        ],
        predicted_failures=[
            PredictedFailureV2(
                type=p.type,
                invariant=p.invariant,
                probability=p.probability,
                horizon=p.horizon,
            )
            for p in state.predicted_failures
        ],
        recommended_actions=[
            RecommendedActionV2(type=a.type, target=a.target, urgency=a.urgency)
            for a in state.recommended_actions
        ],
        horizon=DEFAULT_HORIZON,
        lookback_days=lookback_days,
    )
    payload_hash = stable_json_hash(payload.model_dump())
    receipt_id = new_receipt_id("crr")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return RiskReceiptV2(
        receipt_id=receipt_id,
        runtime=RISK_RUNTIME_NAME,
        timestamp=ts,
        action_type="constitutional_risk_forecast",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="forecast",
            result_hash=payload_hash,
            notes=f"risk_score={state.risk_score:.2f} scope={state.scope.runtime}/{state.scope.invariant}",
        ),
        invariant=InvariantBlockV2(
            name=RISK_INVARIANT,
            description="Risk forecasts are evidence-derived, receipted, and non-binding",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"risk-evidence-{state.state_id}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source=RISK_RUNTIME_NAME,
            jurisdiction="governance",
            legitimacy_basis="constitutional_risk_forecast",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance_only"],
            scope_out=["execution", "state_mutation"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="ConstitutionalSteward"),
        signatures=SignaturesBlockV2(runtime_signature="sig-crr-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected=None,
        ),
        observation=ObservationPayloadV2(
            observed_status="forecast",
            observed_at=ts,
            observer_jurisdiction="constitutional_risk",
            notes=f"predicted_failures={len(state.predicted_failures)}",
        ),
        constitutional_risk=payload,
    )


class ConstitutionalRiskRuntime:
    """Governed forecaster — reads receipts + constitutional state, emits risk observations."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def _global_state(self) -> GlobalConstitutionalState | None:
        try:
            state = self.csr.get_global_snapshot()
            if isinstance(state, GlobalConstitutionalState):
                return state
        except KeyError:
            return None
        return None

    def forecast(
        self,
        *,
        snapshot_at: datetime | None = None,
        lookback: timedelta = DEFAULT_LOOKBACK,
        scopes: list[ConstitutionalRiskScope] | None = None,
    ) -> list[ConstitutionalRiskState]:
        now = snapshot_at or datetime.now(UTC)
        start = now - lookback
        receipts = self.csr.get_all_receipts(before=now)
        global_state = self._global_state()
        target_scopes = scopes or discover_risk_scopes(receipts, global_state)

        forecasts: list[ConstitutionalRiskState] = []
        for scope in target_scopes:
            metrics = _scope_metrics(
                receipts,
                runtime=scope.runtime,
                invariant=scope.invariant,
                start=start,
                end=now,
                now=now,
            )
            forecasts.append(
                build_risk_state(scope=scope, snapshot_at=now, metrics=metrics)
            )
        return forecasts

    def forecast_and_emit(
        self,
        *,
        snapshot_at: datetime | None = None,
        lookback: timedelta = DEFAULT_LOOKBACK,
        scopes: list[ConstitutionalRiskScope] | None = None,
    ) -> list[RiskReceiptV2]:
        """Emit RiskReceiptV2 for each scope — does not apply legal transitions."""
        states = self.forecast(snapshot_at=snapshot_at, lookback=lookback, scopes=scopes)
        emitted: list[RiskReceiptV2] = []
        lookback_days = max(1, int(lookback.total_seconds() // 86400))

        for state in states:
            receipt = build_risk_receipt(
                state,
                previous_receipt_id=self._last_receipt_id,
                previous_lineage_hash=self._last_lineage_hash,
                lookback_days=lookback_days,
            )
            self.csr.put_domain_doc(state.state_id, "constitutional_risk", state)
            self.csr.append_observation_receipt(receipt)
            self._last_receipt_id = receipt.receipt_id
            self._last_lineage_hash = receipt.continuity.lineage_hash
            emitted.append(receipt)

        return emitted


def refresh_constitutional_risk_forecasts() -> None:
    """Run risk forecasts for each runtime CSR (after constitutional state refresh)."""
    from constitutional.runtime.governance_gate import collect_runtime_csrs

    for _name, csr in collect_runtime_csrs():
        try:
            ConstitutionalRiskRuntime(csr).forecast_and_emit()
        except Exception:
            continue


def global_risk_score(csr: ConstitutionalStateRuntime) -> float:
    """Highest scope risk score from the latest forecast pass (v0 helper)."""
    forecasts = ConstitutionalRiskRuntime(csr).forecast()
    if not forecasts:
        return 0.0
    return max(f.risk_score for f in forecasts)
