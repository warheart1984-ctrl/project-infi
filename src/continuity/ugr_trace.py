"""UGR invariant enforcement for CCS ContinuityTrace objects."""

from __future__ import annotations

from typing import Any

from src.continuity.ccs import (
    CCSStore,
    ContinuityTrace,
    continuity_trace_fingerprint,
    law_surface_has_law,
    replay_trace_from_store,
)

INVARIANT_IDS = (
    "ugr.identity_continuity",
    "ugr.authority_continuity",
    "ugr.duality.bidirectional_coherence",
    "ugr.duality.symmetric_constraints",
    "ugr.evidence_integrity",
    "ugr.law_surface_binding",
    "ugr.continuity_unifier",
)


def _status(passed: bool, detail: str) -> dict[str, str]:
    return {"status": "pass" if passed else "fail", "detail": detail}


def is_trace_complete(store: CCSStore, trace: ContinuityTrace) -> bool:
    for identity_id in trace.scope.get("identity_ids", []):
        if identity_id not in store.identities:
            return False
    for event_id in trace.scope.get("event_ids", []):
        if event_id not in store.events:
            return False
    for item in trace.timeline:
        if item["event_id"] not in store.events:
            return False
        for evaluation_id in item.get("evaluations", []):
            if evaluation_id not in store.evaluations:
                return False
        for evidence_id in item.get("evidence", []):
            if evidence_id not in store.evidence:
                return False
    return True


def evaluate_trace_ugr_invariants(store: CCSStore, trace: ContinuityTrace) -> dict[str, dict[str, str]]:
    """Evaluate UGR invariants for a ContinuityTrace within a CCS store."""
    results: dict[str, dict[str, str]] = {}

    identity_ids = list(trace.scope.get("identity_ids", []))
    identity_ok = bool(identity_ids) and all(iid in store.identities for iid in identity_ids)
    unique_ids = len(identity_ids) == len(set(identity_ids))
    results["ugr.identity_continuity"] = _status(
        identity_ok and unique_ids,
        f"identity_count={len(identity_ids)}, resolved={identity_ok}",
    )

    authority_ok = True
    authority_detail: list[str] = []
    for item in trace.timeline:
        event = store.events.get(item["event_id"])
        if event is None:
            authority_ok = False
            continue
        for actor_id in event.actors:
            if actor_id not in store.identities:
                authority_ok = False
                authority_detail.append(f"missing_actor:{actor_id}")
        for evaluation_id in item.get("evaluations", []):
            evaluation = store.evaluations.get(evaluation_id)
            if evaluation is None or evaluation.evaluator_id not in store.identities:
                authority_ok = False
                authority_detail.append(f"missing_evaluator:{evaluation_id}")
    results["ugr.authority_continuity"] = _status(
        authority_ok,
        "; ".join(authority_detail) if authority_detail else "authority chain resolved",
    )

    replayed = replay_trace_from_store(store, trace)
    replay_fp = continuity_trace_fingerprint(replayed)
    original_fp = continuity_trace_fingerprint(trace)
    coherence_ok = replay_fp == original_fp
    results["ugr.duality.bidirectional_coherence"] = _status(
        coherence_ok,
        f"replay_fp_match={coherence_ok}",
    )

    trace_laws = trace.law_surfaces
    symmetric_ok = law_surface_has_law(trace_laws)
    for item in trace.timeline:
        event = store.events[item["event_id"]]
        if not law_surface_has_law(event.law_surface):
            symmetric_ok = False
        for evaluation_id in item.get("evaluations", []):
            evaluation = store.evaluations.get(evaluation_id)
            if evaluation is None or not law_surface_has_law(evaluation.law_surface):
                symmetric_ok = False
    results["ugr.duality.symmetric_constraints"] = _status(
        symmetric_ok,
        "law surfaces present on trace and events",
    )

    evidence_ok = True
    for item in trace.timeline:
        for evidence_id in item.get("evidence", []):
            evidence = store.evidence[evidence_id]
            if not evidence.integrity.get("hash") or not evidence.integrity.get("algorithm"):
                evidence_ok = False
            if not evidence.linked_identity_ids and not evidence.linked_event_ids:
                evidence_ok = False
    results["ugr.evidence_integrity"] = _status(
        evidence_ok,
        f"timeline_evidence_checked={sum(len(i.get('evidence', [])) for i in trace.timeline)}",
    )

    law_ok = law_surface_has_law(trace.law_surfaces) and is_trace_complete(store, trace)
    results["ugr.law_surface_binding"] = _status(
        law_ok,
        f"complete={is_trace_complete(store, trace)}",
    )

    component_pass = all(
        results[iid]["status"] == "pass"
        for iid in INVARIANT_IDS
        if iid != "ugr.continuity_unifier"
    )
    results["ugr.continuity_unifier"] = _status(
        component_pass,
        "all invariants satisfied" if component_pass else "one or more invariants failed",
    )

    return results


def valid_continuity_trace(store: CCSStore, trace: ContinuityTrace) -> bool:
    """Valid(CT) ⇔ complete ∧ invariant-satisfying ∧ replay-stable."""
    if not is_trace_complete(store, trace):
        return False
    report = evaluate_trace_ugr_invariants(store, trace)
    return all(entry["status"] == "pass" for entry in report.values())


def trace_continuity_score(report: dict[str, dict[str, str]]) -> float:
    """Average pass rate across component invariants (excluding unifier)."""
    component_ids = [iid for iid in INVARIANT_IDS if iid != "ugr.continuity_unifier"]
    if not component_ids:
        return 0.0
    passes = sum(1 for iid in component_ids if report.get(iid, {}).get("status") == "pass")
    return round(passes / len(component_ids), 6)


def trace_evidence_integrity_score(store: CCSStore, trace: ContinuityTrace) -> float:
    evidence_ids: set[str] = set()
    for item in trace.timeline:
        evidence_ids.update(item.get("evidence", []))
    if not evidence_ids:
        return 0.0
    valid = 0
    for evidence_id in evidence_ids:
        evidence = store.evidence[evidence_id]
        if evidence.integrity.get("hash") and (
            evidence.linked_identity_ids or evidence.linked_event_ids
        ):
            valid += 1
    return round(valid / len(evidence_ids), 6)


def trace_authority_chain_strength(store: CCSStore, trace: ContinuityTrace) -> float:
    checks = 0
    passed = 0
    for item in trace.timeline:
        event = store.events[item["event_id"]]
        for actor_id in event.actors:
            checks += 1
            if actor_id in store.identities:
                passed += 1
        for evaluation_id in item.get("evaluations", []):
            checks += 1
            evaluation = store.evaluations.get(evaluation_id)
            if evaluation and evaluation.evaluator_id in store.identities:
                passed += 1
    if checks == 0:
        return 0.0
    return round(passed / checks, 6)
