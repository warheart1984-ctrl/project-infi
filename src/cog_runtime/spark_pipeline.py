"""Spark v1 ignition sequence — constitutional turn composition."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.coherence_projection import (
    build_coherence_projection,
    build_coherence_projection_from_cortex,
    format_coherence_projection_block,
)
from src.cog_runtime.formal.distributed_ledger import (
    merge_ledger_entries_monotonic,
    stamp_ledger_entry,
)
from src.cog_runtime.formal.generation_gate import (
    authoritative_emit_or_halt,
    verify_finalized_response,
)
from src.cog_runtime.formal.intent_narrative_reconcile import reconcile_intent_narrative
from src.cog_runtime.formal.spine_pipeline import evaluate_spine_pipeline, halt_receipt
from src.cog_runtime.formal.turn_agency import (
    AgencyViolation,
    capture_turn_boundary,
    reconcile_turn_agency,
)
from src.cog_runtime.tuning import apply_performance_tuning, compute_performance_score

SPARK_PIPELINE_ID = "nova.spark.v1"
SPARK_STAGES: tuple[str, ...] = (
    "spine",
    "aris",
    "jarvis",
    "cortex",
    "coherence_projection",
    "generation_gate",
    "agency_preservation",
    "ledger_append",
    "speaking_emit",
)


def _cortex_state_from_session(session) -> dict[str, Any]:
    metadata = dict(getattr(session, "metadata", {}) or {})
    stored = dict(metadata.get("nova_cognitive_session") or {})
    artifacts = dict(metadata.get("cognitive_runtime_artifacts") or stored.get("artifacts") or {})
    return {
        "artifacts": artifacts,
        "memory_cues": metadata.get("cortex_memory_cues") or [],
        "intent_summary": dict(metadata.get("nova_intent") or artifacts.get("intent_artifact") or {}),
        "narrative_frame": dict(metadata.get("nova_narrative") or artifacts.get("narrative_artifact") or {}),
        "focus_artifact": artifacts.get("focus_artifact"),
        "delib_summary": artifacts.get("decision_object"),
        "ledger": list(stored.get("ledger") or metadata.get("cognitive_runtime_ledger") or []),
        "active_runtimes": list(stored.get("active_runtimes") or []),
    }


def project_coherence_after_cortex(session) -> dict[str, Any] | None:
    """Stage 1 — export bounded read-only cognitive state for the LLM renderer."""
    metadata = dict(getattr(session, "metadata", {}) or {})
    cortex_state = _cortex_state_from_session(session)
    projection = build_coherence_projection_from_cortex(cortex_state)
    if projection is None:
        projection = build_coherence_projection(metadata)
    if projection is not None:
        session.metadata["coherence_projection"] = projection
        session.metadata["coherence_projection_block"] = format_coherence_projection_block(projection)
    return projection


def evaluate_pre_cortex_spine(
    *,
    metadata: dict[str, Any],
    aris: dict[str, Any],
    companion_turn: bool,
) -> dict[str, Any]:
    """Stages 2–4 — Wolf → ARIS → Jarvis before cortex executes."""
    return evaluate_spine_pipeline(
        {
            "substrate_ok": bool(metadata.get("substrate_ok", True)),
            "governance": metadata.get("policy_status") or {},
            "aris_admission": aris,
            "jarvis_blocked": bool(metadata.get("jarvis_blocked")),
            "policy_status": metadata.get("policy_status") or {},
            "cognitive_runtime_enabled": metadata.get("cognitive_runtime_enabled", True),
            "companion_turn": companion_turn,
            "halt_before_cortex": True,
        }
    )


def evaluate_post_cortex_spine(
    *,
    metadata: dict[str, Any],
    companion_turn: bool,
    speaking_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cortex_execute + Speaking_emit gates after cognition and generation."""
    return evaluate_spine_pipeline(
        {
            "substrate_ok": True,
            "governance": metadata.get("policy_status") or {},
            "aris_admission": {"status": "enforced"},
            "jarvis_blocked": bool(metadata.get("jarvis_blocked")),
            "policy_status": metadata.get("policy_status") or {},
            "cognitive_runtime_enabled": metadata.get("cognitive_runtime_enabled", True),
            "cortex_halted": bool(metadata.get("cortex_halted")),
            "speaking_runtime_enabled": metadata.get("speaking_runtime_enabled"),
            "companion_turn": companion_turn,
            "speaking_validation": speaking_validation or metadata.get("speaking_validation"),
            "speaking_wrap_on_fail": False,
            "halt_before_cortex": False,
        }
    )


def run_agency_preservation(session, *, prior_boundary: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stage 4 — turn-boundary intent/narrative reconciliation."""
    metadata = dict(getattr(session, "metadata", {}) or {})
    before = dict(prior_boundary or metadata.get("turn_boundary_before") or {})
    after = capture_turn_boundary(metadata)
    try:
        report = reconcile_turn_agency(before, after)
    except AgencyViolation as exc:
        report = {
            "valid": False,
            "issues": [str(exc)],
            "rule_id": "turn_agency.v1",
            "violation": exc.to_dict(),
        }
        metadata["agency_violation"] = report
        session.metadata["agency_violation"] = report
        raise
    metadata["turn_boundary_after"] = after
    metadata["intent_narrative_reconciliation"] = report
    session.metadata["turn_boundary_after"] = after
    session.metadata["intent_narrative_reconciliation"] = report
    return report


def append_cortex_ledger_monotonic(session, *, node_id: str = "local") -> dict[str, Any]:
    """Stage 5 — vector-clock merge with append-only monotonicity."""
    metadata = dict(getattr(session, "metadata", {}) or {})
    local = list(metadata.get("cognitive_runtime_ledger") or [])
    remote = list(metadata.get("cognitive_runtime_ledger_remote") or [])
    stamped = [stamp_ledger_entry(entry, node_id=node_id) for entry in local if isinstance(entry, dict)]
    merged, report = merge_ledger_entries_monotonic(stamped, remote, node_id=node_id)
    metadata["cognitive_runtime_ledger"] = merged
    metadata["cognitive_runtime_ledger_merge"] = report
    session.metadata["cognitive_runtime_ledger"] = merged
    session.metadata["cognitive_runtime_ledger_merge"] = report
    stored = dict(metadata.get("nova_cognitive_session") or {})
    if stored:
        stored["ledger"] = merged
        session.metadata["nova_cognitive_session"] = stored
    return report


def run_spark_self_tuning(session) -> dict[str, Any] | None:
    """Stage 6 — performance metric drives bounded self-tuning."""
    metadata = dict(getattr(session, "metadata", {}) or {})
    artifacts = dict(metadata.get("cognitive_runtime_artifacts") or {})
    if not artifacts:
        return None
    verification = metadata.get("output_verification_trace") or {}
    performance = compute_performance_score(
        artifacts,
        verification_trace=verification if isinstance(verification, dict) else None,
    )
    tuned = apply_performance_tuning(
        artifacts,
        prior_tuning=metadata.get("cortex_invariant_tuning"),
        performance=performance,
    )
    metadata["cortex_invariant_tuning"] = tuned
    metadata["cortex_performance"] = performance
    session.metadata["cortex_invariant_tuning"] = tuned
    session.metadata["cortex_performance"] = performance
    return tuned


def gate_speaking_output(
    session,
    user_message: str,
    text: str,
    *,
    max_attempts: int = 3,
    regenerate_fn=None,
) -> tuple[str, dict[str, Any]]:
    """Stage 3 — authoritative generation gate before Speaking emits."""
    return authoritative_emit_or_halt(
        session,
        user_message,
        text,
        max_attempts=max_attempts,
        regenerate_fn=regenerate_fn,
    )


def summarize_spark_trace(trace: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pipeline_id": SPARK_PIPELINE_ID,
        "stages": list(SPARK_STAGES),
        "trace": trace,
    }
