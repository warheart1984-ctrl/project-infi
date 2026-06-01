"""Nova Cortex lobe capability justification — measurable value or sunset."""

from __future__ import annotations

from typing import Any

CAPABILITY_EVIDENCE_STATUSES = ("asserted", "proven", "rejected")
REQUIRED_CAPABILITY_FIELDS = (
    "capability_metric",
    "baseline_substitute",
    "evidence_status",
    "sunset_trigger",
)
OPTIONAL_CAPABILITY_FIELDS = ("capability_role",)

# Canonical matrix — keep in sync with docs/runtime/NOVA_CORTEX.md § Lobe Capability Matrix.
NOVA_LOBE_CAPABILITY_MATRIX: dict[str, dict[str, str]] = {
    "jarvis.reasoning": {
        "capability_role": "executive",
        "capability_metric": (
            "High-impact tool/action paths require a complete OODA packet before execution; "
            "incomplete packets are blocked with inspectable reasons."
        ),
        "baseline_substitute": (
            "Prompt-only routing where goal, route, evidence, and verification are implicit in model text."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": "Never sunset; Jarvis retains constitutional executive authority.",
    },
    "speaking.runtime": {
        "capability_role": "speech",
        "capability_metric": (
            "Every user-visible reply maps to named listen/frame/plan/speak/check stages with "
            "validate_reply() pass rate on governed companion turns."
        ),
        "baseline_substitute": (
            "Raw model completion text without stage trace or alignment check narration."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if validate_reply pass rate on companion fixtures is not above "
            "Jarvis-only baseline for three consecutive proof cycles."
        ),
    },
    "cognitive.attention": {
        "capability_role": "agency",
        "capability_metric": (
            "Downstream lobes receive a stable focus_artifact (primary + secondary + salience) "
            "that improves focus token overlap in delivery vs message-only extraction."
        ),
        "baseline_substitute": (
            "Inline focus extraction inside deliberation or speaking without a shared focus artifact."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if A/B focus overlap on companion decision fixtures does not beat baseline "
            "for three consecutive proof cycles."
        ),
    },
    "cognitive.memory": {
        "capability_role": "agency",
        "capability_metric": (
            "Bounded episodic compression and semantic abstraction improve cue recall precision "
            "vs raw transcript replay under memory law limits."
        ),
        "baseline_substitute": (
            "Last-N message transcript pasted into context without encode/index/retrieve/forget stages."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if recall precision@k on companion fixture tasks does not beat transcript-only "
            "baseline for three consecutive proof cycles."
        ),
    },
    "cognitive.deliberation": {
        "capability_role": "agency",
        "capability_metric": (
            "Decision frames produce a structured decision_object with criteria_scores and "
            "commit_source, enabling deterministic replay on identical inputs."
        ),
        "baseline_substitute": (
            "Single-shot model answer 'pick A or B' without inspectable alternatives or criteria."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if decision consistency and revisit rate on decision fixtures do not beat "
            "single-shot baseline for three consecutive proof cycles."
        ),
    },
    "cognitive.reflection": {
        "capability_role": "agency",
        "capability_metric": (
            "Reflection detects alignment gaps (partial/misaligned) and triggers planning handoff "
            "before delivery expansion on companion turns."
        ),
        "baseline_substitute": (
            "Speaking check stage only, without cross-lobe expected_outcome comparison artifact."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if alignment gap detection rate or post-reply correction yield does not beat "
            "speaking-only check for three consecutive proof cycles."
        ),
    },
    "cognitive.planning": {
        "capability_role": "agency",
        "capability_metric": (
            "Planning binds sequenced next_action and adaptive step chains from reflection/arc "
            "evidence, reducing unfocused multi-topic replies on companion arcs."
        ),
        "baseline_substitute": (
            "One-line next step inferred inline in reflection or speaking plan without step_chains."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if companion arc task completion or focus adherence does not beat "
            "reflection-only next-step baseline for three consecutive proof cycles."
        ),
    },
    "cognitive.execution": {
        "capability_role": "agency",
        "capability_metric": (
            "Execution verifies planned action visibility in delivery with tiered recovery and "
            "safe rollback policy; yields measurable verification_status on every handoff."
        ),
        "baseline_substitute": (
            "Speaking check overlap only, without bind/verify/recover/rollback ledger or rollback_policy."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if verification pass rate or recovery yield does not beat speaking-check-only "
            "baseline for three consecutive proof cycles."
        ),
    },
}

CORTEX_MODULE_CAPABILITY_MATRIX: dict[str, dict[str, str]] = {
    "cortex.arcs": {
        "capability_role": "continuity",
        "capability_metric": (
            "Goal-typed multi-turn arcs persist open threads, hierarchy closure, and prior execution "
            "context across companion turns within bounded turn_count."
        ),
        "baseline_substitute": (
            "Session thread id plus last-N user/assistant messages without arc_id, goal_hierarchy, "
            "or closure state."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if companion multi-turn task success does not beat message-window baseline "
            "for three consecutive proof cycles."
        ),
    },
    "cortex.tuning": {
        "capability_role": "adaptation",
        "capability_metric": (
            "Self-tuning adjusts bounded verification thresholds from execution/reflection evidence "
            "with drift guard and history; improves partial→pass conversion vs fixed thresholds."
        ),
        "baseline_substitute": (
            "Fixed execution_overlap_min and focus_overlap_min constants in execution verification."
        ),
        "evidence_status": "asserted",
        "sunset_trigger": (
            "Sunset if tuned thresholds do not improve verification outcomes vs fixed defaults "
            "for three consecutive proof cycles."
        ),
    },
    "nova.narrative": {
        "capability_role": "continuity_of_self",
        "capability_metric": (
            "Each turn updates active_story, becoming, working_on, open_threads, promises, and "
            "last_growth — giving meaning to memory, planning, and arc data without duplicating them."
        ),
        "baseline_substitute": (
            "Arc open_threads plus planning next_action plus memory cues without a narrative "
            "becoming/chapter/growth layer."
        ),
        "evidence_status": "proven",
        "sunset_trigger": (
            "Sunset if operator-rated continuity on companion fixtures does not beat "
            "arc+planning-only baseline for three consecutive proof cycles."
        ),
    },
    "nova.intent": {
        "capability_role": "agency_and_tension",
        "capability_metric": (
            "Maintains active_commitments, protected_values, long_horizon_goals, and current_tensions "
            "across interruptions; commitments survive when narrative active_story changes."
        ),
        "baseline_substitute": (
            "Planning next_action plus arc root_goal without enduring commitments or explicit "
            "tension poles consulted by other lobes."
        ),
        "evidence_status": "proven",
        "sunset_trigger": (
            "Sunset if commitment survival across story-change fixtures does not beat "
            "planning-only baseline for three consecutive proof cycles."
        ),
    },
}

REGISTERED_RUNTIME_IDS = frozenset(NOVA_LOBE_CAPABILITY_MATRIX)


def lobe_capability_contract(runtime_id: str) -> dict[str, str]:
    """Return capability justification fields for a registered Nova lobe."""
    entry = NOVA_LOBE_CAPABILITY_MATRIX.get(runtime_id)
    if entry is None:
        raise KeyError(f"unknown lobe for capability contract: {runtime_id}")
    return {field: str(entry[field]) for field in REQUIRED_CAPABILITY_FIELDS + ("capability_role",) if field in entry}


def cortex_module_capability_contract(module_id: str) -> dict[str, str]:
    entry = CORTEX_MODULE_CAPABILITY_MATRIX.get(module_id)
    if entry is None:
        raise KeyError(f"unknown cortex module for capability contract: {module_id}")
    return {field: str(entry[field]) for field in REQUIRED_CAPABILITY_FIELDS + ("capability_role",) if field in entry}


def validate_runtime_capability_spec(runtime: dict[str, Any]) -> dict[str, Any]:
    """Validate one runtime spec carries a justified capability contract."""
    issues: list[str] = []
    runtime_id = str(runtime.get("id") or "")
    if not runtime_id:
        issues.append("missing_runtime_id")
        return {"valid": False, "issues": issues, "runtime_id": runtime_id}

    for field in REQUIRED_CAPABILITY_FIELDS:
        value = str(runtime.get(field) or "").strip()
        if not value:
            issues.append(f"missing_{field}")
        elif field in {"capability_metric", "baseline_substitute"} and len(value) < 20:
            issues.append(f"{field}_too_short")

    evidence = str(runtime.get("evidence_status") or "")
    if evidence not in CAPABILITY_EVIDENCE_STATUSES:
        issues.append("invalid_evidence_status")

    canonical = NOVA_LOBE_CAPABILITY_MATRIX.get(runtime_id)
    if canonical is None:
        issues.append("runtime_not_in_capability_matrix")
    else:
        for field in REQUIRED_CAPABILITY_FIELDS:
            spec_value = str(runtime.get(field) or "").strip()
            matrix_value = str(canonical.get(field) or "").strip()
            if spec_value and matrix_value and spec_value != matrix_value:
                issues.append(f"{field}_matrix_drift")

    return {"valid": not issues, "issues": issues, "runtime_id": runtime_id}


def validate_cortex_module_capability_matrix() -> dict[str, Any]:
    issues: list[str] = []
    for module_id, entry in CORTEX_MODULE_CAPABILITY_MATRIX.items():
        for field in REQUIRED_CAPABILITY_FIELDS:
            value = str(entry.get(field) or "").strip()
            if not value:
                issues.append(f"{module_id}:missing_{field}")
            elif field in {"capability_metric", "baseline_substitute"} and len(value) < 20:
                issues.append(f"{module_id}:{field}_too_short")
        evidence = str(entry.get("evidence_status") or "")
        if evidence not in CAPABILITY_EVIDENCE_STATUSES:
            issues.append(f"{module_id}:invalid_evidence_status")
    return {"valid": not issues, "issues": issues, "module_count": len(CORTEX_MODULE_CAPABILITY_MATRIX)}


def validate_nova_cortex_capability_governance(family_spec: dict[str, Any]) -> dict[str, Any]:
    """Validate family manifest: every lobe justified; matrix complete vs registered runtimes."""
    issues: list[str] = []
    runtimes = family_spec.get("runtimes")
    if not isinstance(runtimes, list):
        issues.append("missing_runtimes")
        return {"valid": False, "issues": issues}

    runtime_ids = set()
    for runtime in runtimes:
        if not isinstance(runtime, dict):
            issues.append("invalid_runtime_entry")
            continue
        runtime_id = str(runtime.get("id") or "")
        runtime_ids.add(runtime_id)
        result = validate_runtime_capability_spec(runtime)
        if not result["valid"]:
            for item in result["issues"]:
                issues.append(f"{runtime_id}:{item}")

    missing_matrix = sorted(REGISTERED_RUNTIME_IDS - runtime_ids)
    if missing_matrix:
        issues.append(f"missing_registered_runtimes:{','.join(missing_matrix)}")

    extra = sorted(runtime_ids - REGISTERED_RUNTIME_IDS)
    if extra:
        issues.append(f"unregistered_runtimes_in_family:{','.join(extra)}")

    module_result = validate_cortex_module_capability_matrix()
    if not module_result["valid"]:
        issues.extend(module_result["issues"])

    return {
        "valid": not issues,
        "issues": issues,
        "runtime_count": len(runtime_ids),
        "matrix_runtime_count": len(REGISTERED_RUNTIME_IDS),
        "cortex_module_count": len(CORTEX_MODULE_CAPABILITY_MATRIX),
    }
