"""ArtifactType vs ActionType — enforce cortex lobes do not emit executable actions."""

from __future__ import annotations

from typing import Any

ARTIFACT_TYPE_MEMBERS: frozenset[str] = frozenset(
    {
        "focus_artifact",
        "memory_artifact",
        "decision_object",
        "reflection_artifact",
        "planning_artifact",
        "execution_artifact",
        "intent_artifact",
        "narrative_artifact",
        "cognitive_arc",
        "invariant_tuning_artifact",
        "retrieved_cues",
        "focus_signals",
    }
)

ACTION_TYPE_MEMBERS: frozenset[str] = frozenset(
    {
        "tool_call",
        "shell_command",
        "file_write",
        "file_delete",
        "network_request",
        "provider_generate",
        "god_brain_execute",
        "policy_override",
    }
)

# Lobe declared output keys must be artifacts, never actions.
LOBE_OUTPUT_KEY_PATTERN = "_artifact|_object|_cues|_signals|_arc"


def validate_cortex_output_typing(family_spec: dict[str, Any]) -> dict[str, Any]:
    """Governance gate: every lobe output key ∈ ArtifactType, none ∈ ActionType."""
    issues: list[str] = []
    runtimes = family_spec.get("runtimes") or family_spec.get("family_runtimes") or []
    if isinstance(runtimes, dict):
        runtimes = list(runtimes.values())

    for runtime in runtimes:
        if not isinstance(runtime, dict):
            continue
        runtime_id = str(runtime.get("id") or "")
        outputs = runtime.get("outputs") or {}
        if not isinstance(outputs, dict):
            continue
        for key in outputs:
            key_str = str(key)
            if key_str in ACTION_TYPE_MEMBERS:
                issues.append(f"action_output:{runtime_id}:{key_str}")
            if key_str.endswith("_action") or key_str.endswith("_execute"):
                issues.append(f"suspected_action_output:{runtime_id}:{key_str}")

    modules = family_spec.get("cortex_modules") or []
    if isinstance(modules, dict):
        modules = list(modules.values())
    for module in modules:
        if not isinstance(module, dict):
            continue
        module_id = str(module.get("id") or "")
        outputs = module.get("outputs") or {}
        if not isinstance(outputs, dict):
            continue
        for key in outputs:
            key_str = str(key)
            if key_str in ACTION_TYPE_MEMBERS:
                issues.append(f"action_output:{module_id}:{key_str}")

    return {
        "valid": not issues,
        "issues": issues,
        "artifact_type_count": len(ARTIFACT_TYPE_MEMBERS),
        "action_type_count": len(ACTION_TYPE_MEMBERS),
        "theorem": "5.1_artifact_only_outputs",
    }


def output_type_governance_spec() -> dict[str, Any]:
    return {
        "schema_id": "nova.output_type_governance.v1",
        "artifact_type": sorted(ARTIFACT_TYPE_MEMBERS),
        "action_type": sorted(ACTION_TYPE_MEMBERS),
        "theorem_5_1": (
            "For all lobes R_i in Nova Cortex, ο_i(Σ_i) ⊂ ArtifactType, not ActionType. "
            "Jarvis Reasoning Runtime alone may produce ActionType proposals subject to OODA gate."
        ),
        "enforcement": (
            "Boot/CI gate validate_cortex_output_typing(); runtime lobes consult-only per MA-13."
        ),
    }
