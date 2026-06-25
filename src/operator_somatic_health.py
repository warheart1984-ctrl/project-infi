"""Unified operator/system somatic health map (Release 32 proprioception)."""

# Mythic: Operator Somatic Health
# Engineering: OperatorSomaticHealthEngine
from __future__ import annotations

from typing import Any


def build_somatic_health_snapshot() -> dict[str, Any]:
    """Read-only aggregation of seam, sentinel, doctor, fabric, and substrate posture."""
    seam = _safe_seam_health()
    monitoring = _safe_monitoring()
    doctor = _safe_doctor()
    coherence = _safe_coherence_slices()
    substrate = _safe_substrate_posture()
    dreamspace = _safe_dreamspace_posture()
    organ_mesh = _safe_organ_mesh_posture()
    culture = _safe_culture_posture()
    identity = _safe_identity_posture()
    narrative = _safe_narrative_posture()
    autobiographical = _safe_autobiographical_posture()
    social = _safe_social_posture()
    multi_being = _safe_multi_being_posture()
    culture_of_beings = _safe_culture_of_beings_posture()
    ecosystem = _safe_ecosystem_posture()
    governance_membrane = _safe_governance_membrane_posture()
    diplomacy = _safe_diplomacy_posture()
    norm_federation = _safe_norm_federation_posture()
    constitutional_evolution = _safe_constitutional_evolution_posture()
    governed_civilization = _safe_governed_civilization_posture()
    federated_epoch = _safe_federated_epoch_posture()
    overall = _overall_posture(seam, monitoring, doctor, substrate)
    return {
        "somatic_health_version": "operator_somatic_health.v1",
        "overall_posture": overall,
        "seam_health": seam,
        "monitoring": monitoring,
        "doctor": doctor,
        "coherence_slices": coherence,
        "substrate_posture": substrate,
        "dreamspace_posture": dreamspace,
        "organ_mesh_posture": organ_mesh,
        "culture_posture": culture,
        "identity_posture": identity,
        "narrative_posture": narrative,
        "autobiographical_posture": autobiographical,
        "social_posture": social,
        "multi_being_posture": multi_being,
        "culture_of_beings_posture": culture_of_beings,
        "ecosystem_posture": ecosystem,
        "governance_membrane_posture": governance_membrane,
        "diplomacy_posture": diplomacy,
        "norm_federation_posture": norm_federation,
        "constitutional_evolution_posture": constitutional_evolution,
        "governed_civilization_posture": governed_civilization,
        "federated_epoch_posture": federated_epoch,
        "active_mesh_runs": organ_mesh.get("active_mesh_runs", 0),
        "blocked_handoffs": organ_mesh.get("blocked_handoffs", 0),
        "adopted_habits": culture.get("adopted_habits", 0),
        "habit_candidates": culture.get("candidate_habits", 0),
        "adopted_claims": identity.get("adopted_claims", 0),
        "identity_drift_events": identity.get("identity_drift_events", 0),
        "adopted_beats": narrative.get("adopted_beats", 0),
        "narrative_drift_events": narrative.get("narrative_drift_events", 0),
        "adopted_episodes": autobiographical.get("adopted_episodes", 0),
        "autobiographical_drift_events": autobiographical.get("autobiographical_drift_events", 0),
        "ongoing_work_count": autobiographical.get("ongoing_work_count", 0),
        "adopted_bonds": social.get("adopted_bonds", 0),
        "social_drift_events": social.get("social_drift_events", 0),
        "federated_peer_count": social.get("federated_peer_count", 0),
        "adopted_pacts": multi_being.get("adopted_pacts", 0),
        "multi_being_drift_events": multi_being.get("multi_being_drift_events", 0),
        "cross_organism_peer_count": multi_being.get("cross_organism_peer_count", 0),
        "adopted_norms": culture_of_beings.get("adopted_norms", 0),
        "culture_of_beings_drift_events": culture_of_beings.get("culture_of_beings_drift_events", 0),
        "adopted_charters": ecosystem.get("adopted_charters", 0),
        "ecosystem_drift_events": ecosystem.get("ecosystem_drift_events", 0),
        "adopted_membrane_policies": governance_membrane.get("adopted_policies", 0),
        "membrane_drift_events": governance_membrane.get("membrane_drift_events", 0),
        "adopted_accords": diplomacy.get("adopted_accords", 0),
        "adopted_treaties": norm_federation.get("adopted_treaties", 0),
        "adopted_amendments": constitutional_evolution.get("adopted_amendments", 0),
        "adopted_civilizations": governed_civilization.get("adopted_civilizations", 0),
        "adopted_federated_epoch_charters": federated_epoch.get("adopted_charters", 0),
        "read_only": True,
        "claim_label": "asserted",
    }


def _safe_seam_health() -> dict[str, Any]:
    try:
        from src.operator_infinity1_dashboard import build_seam_health_poll

        return build_seam_health_poll()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_monitoring() -> dict[str, Any]:
    try:
        from src.operator_infinity1_dashboard import build_monitoring_poll

        return build_monitoring_poll()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_doctor() -> dict[str, Any]:
    try:
        from src.aais_doctor_organ import build_aais_doctor_status

        return build_aais_doctor_status()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_coherence_slices() -> dict[str, Any]:
    try:
        from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

        fabric = build_coherence_fabric_status()
        return {
            "immune_observe_posture": fabric.get("immune_observe_posture"),
            "story_forge_execution_layer": fabric.get("story_forge_execution_layer"),
            "predictive_lane_posture": fabric.get("predictive_lane_posture"),
            "product_shell_posture": fabric.get("product_shell_posture"),
            "organ_mesh_posture": fabric.get("organ_mesh_posture"),
            "culture_posture": fabric.get("culture_posture"),
            "identity_posture": fabric.get("identity_posture"),
            "narrative_posture": fabric.get("narrative_posture"),
            "autobiographical_posture": fabric.get("autobiographical_posture"),
            "social_posture": fabric.get("social_posture"),
            "multi_being_posture": fabric.get("multi_being_posture"),
            "culture_of_beings_posture": fabric.get("culture_of_beings_posture"),
            "ecosystem_posture": fabric.get("ecosystem_posture"),
            "governance_membrane_posture": fabric.get("governance_membrane_posture"),
        }
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_substrate_posture() -> dict[str, Any]:
    try:
        from app.db import count_stale_otem_approvals, list_pending_workflow_approvals

        pending = list_pending_workflow_approvals(limit=200)
        otem_pending = [p for p in pending if p.get("step_type") == "otem_execution_substrate"]
        return {
            "pending_otem_approvals": len(otem_pending),
            "stale_otem_approvals": count_stale_otem_approvals(),
            "durable_substrate_enabled": True,
        }
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_dreamspace_posture() -> dict[str, Any]:
    try:
        from src.dreamspace_organ import build_dreamspace_organ_status

        return build_dreamspace_organ_status()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_organ_mesh_posture() -> dict[str, Any]:
    try:
        from src.organ_coordination_runtime import organ_coordination_runtime

        return organ_coordination_runtime.mesh_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_culture_posture() -> dict[str, Any]:
    try:
        from src.culture_habit_runtime import culture_habit_runtime

        return culture_habit_runtime.culture_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_identity_posture() -> dict[str, Any]:
    try:
        from src.identity_self_model_runtime import identity_self_model_runtime

        return identity_self_model_runtime.identity_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_narrative_posture() -> dict[str, Any]:
    try:
        from src.narrative_continuity_runtime import narrative_continuity_runtime

        return narrative_continuity_runtime.narrative_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_autobiographical_posture() -> dict[str, Any]:
    try:
        from src.autobiographical_agency_runtime import autobiographical_agency_runtime

        return autobiographical_agency_runtime.autobiographical_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_social_posture() -> dict[str, Any]:
    try:
        from src.social_continuity_runtime import social_continuity_runtime

        return social_continuity_runtime.social_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_multi_being_posture() -> dict[str, Any]:
    try:
        from src.multi_being_continuity_runtime import multi_being_continuity_runtime

        return multi_being_continuity_runtime.multi_being_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_culture_of_beings_posture() -> dict[str, Any]:
    try:
        from src.culture_of_beings_runtime import culture_of_beings_runtime

        return culture_of_beings_runtime.culture_of_beings_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_ecosystem_posture() -> dict[str, Any]:
    try:
        from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

        return constitutional_ecosystem_runtime.ecosystem_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_governance_membrane_posture() -> dict[str, Any]:
    try:
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        return multi_organism_governance_membrane_runtime.membrane_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_diplomacy_posture() -> dict[str, Any]:
    try:
        from src.diplomacy.runtime import inter_substrate_diplomacy_runtime

        return inter_substrate_diplomacy_runtime.diplomacy_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_norm_federation_posture() -> dict[str, Any]:
    try:
        from src.norm_federation_runtime import norm_federation_runtime

        return norm_federation_runtime.federation_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_constitutional_evolution_posture() -> dict[str, Any]:
    try:
        from src.constitutional_evolution_runtime import constitutional_evolution_runtime

        return constitutional_evolution_runtime.evolution_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_governed_civilization_posture() -> dict[str, Any]:
    try:
        from src.governed_civilization_runtime import governed_civilization_runtime

        return governed_civilization_runtime.civilization_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _safe_federated_epoch_posture() -> dict[str, Any]:
    try:
        from src.federated_civilizational_epoch_runtime import federated_civilizational_epoch_runtime

        return federated_civilizational_epoch_runtime.epoch_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "degraded": True}


def _overall_posture(
    seam: dict[str, Any],
    monitoring: dict[str, Any],
    doctor: dict[str, Any],
    substrate: dict[str, Any],
) -> str:
    if seam.get("degraded") or monitoring.get("degraded") or doctor.get("degraded"):
        return "degraded"
    if int(substrate.get("stale_otem_approvals") or 0) > 0:
        return "attention_required"
    if seam.get("healthy") is False:
        return "unhealthy"
    return "nominal"
