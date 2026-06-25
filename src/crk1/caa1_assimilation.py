"""CAA-1 / CXD-1 — Continuity Assimilation Artifact / Continuity Demonstration Receipt."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.crk1.schema_validator import CRK1SchemaValidator

DEFAULT_ASSIMILATION_THRESHOLD = 0.15


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(payload: str | bytes | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = payload
    return hashlib.sha256(body).hexdigest()


@dataclass
class JudgmentQualitySample:
    """Mission harness judgment-quality metric Q ∈ [0, 1]."""

    steward_id: str
    contradiction_class: str
    prediction_error: float
    calibration_aligned: bool
    trace: dict[str, Any] = field(default_factory=dict)

    def quality(self) -> float:
        error_penalty = max(0.0, min(1.0, self.prediction_error))
        alignment_bonus = 0.25 if self.calibration_aligned else 0.0
        return max(0.0, min(1.0, 1.0 - error_penalty + alignment_bonus))

    def judgment_hash(self) -> str:
        return sha256_hex(
            {
                "steward_id": self.steward_id,
                "contradiction_class": self.contradiction_class,
                "prediction_error": self.prediction_error,
                "calibration_aligned": self.calibration_aligned,
                "trace": self.trace,
            }
        )


@dataclass
class AssimilationContext:
    steward_id: str
    original_participant_ids: list[str]
    crr_hash: str
    clg_hash: str
    contradiction_class: str
    pre_sample: JudgmentQualitySample
    post_sample: JudgmentQualitySample
    assimilation_threshold: float = DEFAULT_ASSIMILATION_THRESHOLD
    replay_evidence: dict[str, Any] = field(default_factory=dict)


def compute_isolation_proof(
    steward_id: str,
    original_participant_ids: list[str],
    *,
    mission_id: str = "MISSION-006",
) -> str:
    if steward_id in original_participant_ids:
        raise ValueError(f"steward {steward_id} participated in original calibration; isolation failed")
    return sha256_hex(
        {
            "steward_id": steward_id,
            "original_participants": sorted(original_participant_ids),
            "isolated": True,
            "mission_id": mission_id,
        }
    )


def compute_assimilation_delta(pre: JudgmentQualitySample, post: JudgmentQualitySample) -> float:
    return post.quality() - pre.quality()


def compute_receipt_proof_bundle(receipt: dict[str, Any]) -> str:
    """Recompute proof bundle from public receipt fields (governance validation)."""
    return sha256_hex(
        {
            "cxd_id": receipt["cxd_id"],
            "steward_id": receipt["steward_id"],
            "isolation_proof": receipt["isolation_proof"],
            "lineage_used": receipt["lineage_used"],
            "pre_assimilation_judgment": receipt["pre_assimilation_judgment"],
            "post_assimilation_judgment": receipt["post_assimilation_judgment"],
            "assimilation_delta": receipt["assimilation_delta"],
            "assimilation_threshold": receipt["assimilation_threshold"],
            "continuity_passed": receipt["continuity_passed"],
        }
    )


def build_caa1_receipt(ctx: AssimilationContext) -> dict[str, Any]:
    isolation = compute_isolation_proof(ctx.steward_id, ctx.original_participant_ids)
    q_pre = ctx.pre_sample.quality()
    q_post = ctx.post_sample.quality()
    delta = q_post - q_pre
    continuity_passed = delta >= ctx.assimilation_threshold

    pre_hash = ctx.pre_sample.judgment_hash()
    post_hash = ctx.post_sample.judgment_hash()

    cxd_id = str(uuid.uuid4())
    receipt_without_bundle = {
        "cxd_id": cxd_id,
        "steward_id": ctx.steward_id,
        "isolation_proof": isolation,
        "lineage_used": {
            "crr_hash": ctx.crr_hash,
            "clg_hash": ctx.clg_hash,
        },
        "pre_assimilation_judgment": pre_hash,
        "post_assimilation_judgment": post_hash,
        "assimilation_delta": round(delta, 6),
        "assimilation_threshold": ctx.assimilation_threshold,
        "continuity_passed": continuity_passed,
    }
    proof_bundle = compute_receipt_proof_bundle(receipt_without_bundle)

    receipt = {
        **receipt_without_bundle,
        "timestamp": _now_iso(),
        "proof_bundle": proof_bundle,
    }
    return receipt


def validate_caa1(receipt: dict[str, Any]) -> None:
    CRK1SchemaValidator().validate("CAA1ContinuityAssimilationReceipt", receipt)
    expected_passed = receipt["assimilation_delta"] >= receipt["assimilation_threshold"]
    if receipt["continuity_passed"] != expected_passed:
        raise ValueError(
            "continuity_passed inconsistent with assimilation_delta and assimilation_threshold"
        )
    if receipt["proof_bundle"] != compute_receipt_proof_bundle(receipt):
        raise ValueError("proof_bundle does not match receipt fields")
