"""Tests for Constitutional Risk Runtime (governed forecaster)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.global_constitutional_state import ConstitutionalStateAggregator
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    DivergencePayloadV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    RemediationPayloadV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    is_receipt_v2_complete,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.risk_runtime import (
    ConstitutionalRiskRuntime,
    ConstitutionalRiskScope,
    compute_scope_risk_score,
    predict_failures,
    _ScopeMetrics,
)


def _blocks(*, request_id: str = "task-1") -> dict:
    payload_hash = stable_json_hash({"request_id": request_id})
    receipt_id = new_receipt_id("test")
    return {
        "inputs": ReceiptInputsV2(
            request_id=request_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=request_id),
        ),
        "outputs": ReceiptOutputsV2(status="ok", result_hash=payload_hash),
        "invariant": InvariantBlockV2(
            name="NO_TRUTH_WITHOUT_VERIFICATION",
            description="test invariant",
            satisfied=False,
        ),
        "evidence": EvidenceBundleV2(
            bundle_id="evb-test",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        "authority": AuthorityBlockV2(
            source="TruthRuntime",
            jurisdiction="test",
            legitimacy_basis="test",
        ),
        "reproducibility": ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        "impact_boundary": ImpactBoundaryV2(scope_in=["test"], scope_out=[]),
        "accountability": AccountabilityBlockV2(primary_accountable_party="operator"),
        "signatures": SignaturesBlockV2(runtime_signature="sig-test"),
        "continuity": ContinuityBlockV2(
            lineage_hash=compute_lineage_hash(
                previous_receipt_id=None,
                receipt_id=receipt_id,
                payload_hash=payload_hash,
            )
        ),
    }


def test_empty_csr_low_global_risk() -> None:
    csr = ConstitutionalStateRuntime()
    ConstitutionalStateAggregator(csr).update_snapshot()
    forecasts = ConstitutionalRiskRuntime(csr).forecast()

    assert forecasts
    global_forecast = next(f for f in forecasts if f.scope.runtime == "__global__")
    assert global_forecast.risk_score < 0.5


def test_divergence_increases_scope_risk() -> None:
    csr = ConstitutionalStateRuntime()
    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    blocks = _blocks(request_id="mission-42")

    for i in range(4):
        ts = (now - timedelta(days=i)).isoformat().replace("+00:00", "Z")
        csr.append_observation_receipt(
            DivergenceReceiptV2(
                receipt_id=new_receipt_id("div"),
                runtime="TruthRuntime",
                timestamp=ts,
                action_type="divergence_detected",
                lifecycle=LifecycleBlockV2(stage="divergence"),
                divergence=DivergencePayloadV2(nature="verification_failed", magnitude="high"),
                **blocks,
            )
        )

    scope = ConstitutionalRiskScope(runtime="TruthRuntime", invariant="NO_TRUTH_WITHOUT_VERIFICATION")
    forecast = ConstitutionalRiskRuntime(csr).forecast(snapshot_at=now, scopes=[scope])[0]

    assert forecast.risk_score > 0.05
    assert any(f.factor == "unresolved_divergences" and f.value >= 4 for f in forecast.risk_factors)


def test_high_risk_predicts_amendment_when_divergences_accelerate() -> None:
    metrics = _ScopeMetrics(
        divergences=9,
        remediations=2,
        overdue_remediations=3,
        arbitrations=1,
        health_slope=-0.05,
        divergences_increasing=True,
    )
    score, _ = compute_scope_risk_score(metrics)
    assert score > 0.4

    predictions = predict_failures(
        risk_score=0.85,
        metrics=metrics,
        invariant="NO_TRUTH_WITHOUT_VERIFICATION",
    )
    assert any(p.type == "amendment_required" for p in predictions)


def test_forecast_and_emit_does_not_mutate_legal_state() -> None:
    csr = ConstitutionalStateRuntime()
    before_states = len(csr._states)  # noqa: SLF001

    receipts = ConstitutionalRiskRuntime(csr).forecast_and_emit(
        snapshot_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    )

    assert len(receipts) >= 1
    assert is_receipt_v2_complete(receipts[0])
    assert receipts[0].runtime == "ConstitutionalRiskRuntime"
    assert len(csr._states) == before_states  # noqa: SLF001


def test_overdue_remediation_triggers_remediation_failure_prediction() -> None:
    csr = ConstitutionalStateRuntime()
    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)

    for i in range(3):
        old_ts = (now - timedelta(days=10 + i)).isoformat().replace("+00:00", "Z")
        csr.append_observation_receipt(
            RemediationReceiptV2(
                receipt_id=new_receipt_id("rem"),
                runtime="OperatorRuntime",
                timestamp=old_ts,
                action_type="remediation_plan",
                lifecycle=LifecycleBlockV2(stage="remediation"),
                remediation=RemediationPayloadV2(
                    required_actions=["fix divergence"],
                    responsible_party="operator",
                ),
                **_blocks(request_id=f"overdue-task-{i}"),
            )
        )

    scope = ConstitutionalRiskScope(runtime="OperatorRuntime", invariant="NO_TRUTH_WITHOUT_VERIFICATION")
    forecast = ConstitutionalRiskRuntime(csr).forecast(snapshot_at=now, scopes=[scope])[0]

    overdue_factor = next(f for f in forecast.risk_factors if f.factor == "overdue_remediations")
    assert overdue_factor.value >= 3
    assert forecast.risk_score > 0.2

    predictions = predict_failures(
        risk_score=0.75,
        metrics=_ScopeMetrics(
            divergences=2,
            remediations=3,
            overdue_remediations=3,
            arbitrations=0,
            health_slope=0.0,
            divergences_increasing=False,
        ),
        invariant=scope.invariant,
    )
    assert any(p.type == "remediation_failure" for p in predictions)
