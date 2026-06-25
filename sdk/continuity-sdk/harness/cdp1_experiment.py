"""CDP-1 — Continuity Demonstration Protocol experiment harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from src.crk1.caa1_assimilation import (
    AssimilationContext,
    JudgmentQualitySample,
    build_caa1_receipt,
    compute_isolation_proof,
    sha256_hex,
    validate_caa1,
)

from .metrics import JudgmentMetrics, assimilation_delta


class CDP1Steward(Protocol):
    """Steward participating in a CDP-1 run."""

    id: str

    def isolation_material(self) -> str: ...

    def replay_lineage(self, crr: dict[str, Any], clg: dict[str, Any]) -> None: ...


TaskFn = Callable[[CDP1Steward], dict[str, Any]]


@dataclass
class CDP1RunResult:
    q_pre: float
    q_post: float
    delta: float
    pre_trace: dict[str, Any]
    post_trace: dict[str, Any]
    receipt: dict[str, Any]
    continuity_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "Q_pre": self.q_pre,
            "Q_post": self.q_post,
            "delta": self.delta,
            "pre_trace": self.pre_trace,
            "post_trace": self.post_trace,
            "receipt": self.receipt,
            "continuity_passed": self.continuity_passed,
        }


def judgment_quality(trace: dict[str, Any]) -> float:
    metrics = JudgmentMetrics(
        prediction_error=float(trace.get("prediction_error", 1.0)),
        calibration_aligned=bool(trace.get("calibration_aligned", False)),
    )
    return metrics.quality()


def trace_to_sample(
    steward_id: str,
    contradiction_class: str,
    trace: dict[str, Any],
    *,
    phase: str,
) -> JudgmentQualitySample:
    enriched = {**trace, "phase": phase}
    return JudgmentQualitySample(
        steward_id=steward_id,
        contradiction_class=contradiction_class,
        prediction_error=float(trace.get("prediction_error", 1.0)),
        calibration_aligned=bool(trace.get("calibration_aligned", False)),
        trace=enriched,
    )


@dataclass
class CDP1Experiment:
    """Canonical CDP-1 experiment engine (CEP)."""

    task: TaskFn
    threshold: float
    contradiction_class: str = "physics.fall_time"
    original_participant_ids: list[str] = field(default_factory=list)

    def run(
        self,
        steward: CDP1Steward,
        crr: dict[str, Any],
        clg: dict[str, Any],
    ) -> CDP1RunResult:
        # Article II — Isolation (raises if steward participated)
        compute_isolation_proof(steward.id, self.original_participant_ids, mission_id="CDP-1")

        # 1. Pre-measurement
        pre_trace = self.task(steward)
        q_pre = judgment_quality(pre_trace)
        pre_sample = trace_to_sample(
            steward.id, self.contradiction_class, pre_trace, phase="pre_assimilation"
        )

        # 2. Lineage replay
        steward.replay_lineage(crr, clg)

        # 3. Post-measurement
        post_trace = self.task(steward)
        q_post = judgment_quality(post_trace)
        post_sample = trace_to_sample(
            steward.id, self.contradiction_class, post_trace, phase="post_assimilation"
        )

        # 4. Compute ΔA
        delta = assimilation_delta(
            JudgmentMetrics(pre_sample.prediction_error, pre_sample.calibration_aligned),
            JudgmentMetrics(post_sample.prediction_error, post_sample.calibration_aligned),
        )

        crr_hash = sha256_hex(crr)
        clg_hash = sha256_hex(clg)

        # 5. Build CAA-1 receipt
        receipt = build_caa1_receipt(
            AssimilationContext(
                steward_id=steward.id,
                original_participant_ids=list(self.original_participant_ids),
                crr_hash=crr_hash,
                clg_hash=clg_hash,
                contradiction_class=self.contradiction_class,
                pre_sample=pre_sample,
                post_sample=post_sample,
                assimilation_threshold=self.threshold,
                replay_evidence={"cdp1": True, "crr_keys": sorted(crr.keys()), "clg_keys": sorted(clg.keys())},
            )
        )

        return CDP1RunResult(
            q_pre=q_pre,
            q_post=q_post,
            delta=delta,
            pre_trace=pre_trace,
            post_trace=post_trace,
            receipt=receipt,
            continuity_passed=receipt["continuity_passed"],
        )


def validate_cdp1_run(result: CDP1RunResult) -> dict[str, Any]:
    """Governance validation pipeline for a CDP-1 run."""
    report: dict[str, Any] = {"stages": {}, "decision": "FAIL"}

    try:
        validate_caa1(result.receipt)
        report["stages"]["structural"] = "PASS"
    except (ValueError, KeyError) as exc:
        report["stages"]["structural"] = f"FAIL: {exc}"
        return report

    recomputed_delta = result.q_post - result.q_pre
    if abs(recomputed_delta - result.delta) > 1e-6:
        report["stages"]["metric"] = "FAIL: delta mismatch"
        return report
    if result.delta < result.receipt["assimilation_threshold"]:
        report["stages"]["metric"] = "FAIL: delta below threshold"
        return report
    report["stages"]["metric"] = "PASS"

    if result.receipt["proof_bundle"]:
        report["stages"]["proof_bundle"] = "PASS"
    else:
        report["stages"]["proof_bundle"] = "FAIL: missing proof bundle"
        return report

    report["decision"] = "PASS"
    return report
