"""Deterministic convergence of governed lane outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ugr.lane_manager import LANE_PRECEDENCE, LaneResult


CONVERGENCE_ENGINE_ID = "aais.ugr.convergence_engine"
CONVERGENCE_ENGINE_VERSION = "0.1"


def _claim_key(subject: str, predicate: str) -> tuple[str, str]:
    return (
        " ".join(str(subject or "").split()).strip().lower(),
        " ".join(str(predicate or "").split()).strip().lower(),
    )


def _lane_has_hard_fail(lane: dict[str, Any] | LaneResult) -> bool:
    payload = lane.to_dict() if isinstance(lane, LaneResult) else dict(lane or {})
    for item in payload.get("invariant_results") or []:
        if item.get("status") == "hard_fail":
            return True
    for flag in payload.get("immune_flags") or []:
        if str(flag.get("severity") or "").lower() in {"high", "critical"}:
            return True
    return payload.get("status") == "error"


def _collect_claims(lane_results: list[dict[str, Any] | LaneResult]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for lane in lane_results:
        payload = lane.to_dict() if isinstance(lane, LaneResult) else dict(lane or {})
        if _lane_has_hard_fail(payload):
            continue
        for claim in (payload.get("payload") or {}).get("claims") or []:
            collected.append(
                {
                    **dict(claim),
                    "lane_id": payload.get("lane_id"),
                    "lane_type": payload.get("lane_type"),
                }
            )
    return collected


def _best_lane_for_group(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        entries,
        key=lambda item: (
            LANE_PRECEDENCE.get(str(item.get("lane_type") or ""), 0),
            float(item.get("confidence") or 0.0),
            str(item.get("lane_id") or ""),
        ),
    )


class ConvergenceEngine:
    """Merge lane outputs into governed beliefs and plans."""

    def converge(
        self,
        trace_id: str,
        lane_results: list[dict[str, Any] | LaneResult],
        *,
        request: dict[str, Any] | None = None,
        policy_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return converge_lane_results(
            trace_id,
            lane_results,
            request=request,
            policy_context=policy_context,
        )


def converge_lane_results(
    trace_id: str,
    lane_results: list[dict[str, Any] | LaneResult],
    *,
    request: dict[str, Any] | None = None,
    policy_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_lanes = [
        lane.to_dict() if isinstance(lane, LaneResult) else dict(lane or {}) for lane in lane_results
    ]
    invalid_lanes = [lane for lane in normalized_lanes if _lane_has_hard_fail(lane)]
    claims = _collect_claims(normalized_lanes)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for claim in claims:
        key = _claim_key(str(claim.get("subject") or ""), str(claim.get("predicate") or ""))
        grouped.setdefault(key, []).append(claim)

    final_beliefs: list[dict[str, Any]] = []
    uncertainties: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []

    for (subject, predicate), entries in sorted(grouped.items(), key=lambda item: item[0]):
        objects = {str(entry.get("object") or "").strip() for entry in entries if str(entry.get("object") or "").strip()}
        supporting_lanes = sorted({str(entry.get("lane_id") or "") for entry in entries if entry.get("lane_id")})
        if len(objects) > 1:
            winner = _best_lane_for_group(entries)
            contradictions = sorted(
                {str(entry.get("lane_id") or "") for entry in entries if entry is not winner and entry.get("lane_id")}
            )
            final_beliefs.append(
                {
                    "id": f"belief-{subject[:24]}-{predicate[:24]}",
                    "subject": entries[0].get("subject") or subject,
                    "predicate": entries[0].get("predicate") or predicate,
                    "object": winner.get("object"),
                    "confidence": round(float(winner.get("confidence") or 0.0), 3),
                    "supporting_lanes": [str(winner.get("lane_id") or "")],
                    "contradicting_lanes": contradictions,
                    "provenance": list(winner.get("evidence_refs") or []),
                    "status": "contested" if contradictions else "accepted",
                }
            )
            if contradictions:
                uncertainties.append(
                    {
                        "topic": f"{subject} / {predicate}",
                        "reason": "conflicting_lanes",
                        "recommended_followup": "Review lane traces and add graph evidence before acting.",
                    }
                )
                flags.append(
                    {
                        "type": "human_review_recommended",
                        "severity": "medium",
                        "details": f"Lane conflict on {subject} / {predicate}",
                    }
                )
            continue

        if len(entries) >= 2:
            confidence = min(
                0.99,
                sum(float(entry.get("confidence") or 0.0) for entry in entries) / max(1, len(entries)) + 0.08,
            )
        else:
            confidence = float(entries[0].get("confidence") or 0.0)

        final_beliefs.append(
            {
                "id": f"belief-{subject[:24]}-{predicate[:24]}",
                "subject": entries[0].get("subject") or subject,
                "predicate": entries[0].get("predicate") or predicate,
                "object": entries[0].get("object"),
                "confidence": round(confidence, 3),
                "supporting_lanes": supporting_lanes,
                "contradicting_lanes": [],
                "provenance": sorted(
                    {
                        ref
                        for entry in entries
                        for ref in (entry.get("evidence_refs") or [])
                        if ref
                    }
                ),
                "status": "accepted",
            }
        )

    if invalid_lanes:
        flags.append(
            {
                "type": "anomaly_detected",
                "severity": "medium",
                "details": f"{len(invalid_lanes)} lane(s) failed invariant or immune checks",
            }
        )

    if not final_beliefs and not claims:
        flags.append(
            {
                "type": "human_review_recommended",
                "severity": "low",
                "details": "No lane produced acceptable claims.",
            }
        )
        uncertainties.append(
            {
                "topic": str((request or {}).get("question") or "request"),
                "reason": "insufficient_data",
                "recommended_followup": "Add graph evidence or refine the question.",
            }
        )

    return {
        "engine_id": CONVERGENCE_ENGINE_ID,
        "engine_version": CONVERGENCE_ENGINE_VERSION,
        "trace_id": trace_id,
        "final_beliefs": final_beliefs,
        "final_plan": None,
        "uncertainties": uncertainties,
        "flags": flags,
        "invalid_lane_count": len(invalid_lanes),
        "policy_context": dict(policy_context or {}),
    }
