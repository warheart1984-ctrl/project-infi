"""Jarvis Writers 3 Rules guardrail pack."""

from __future__ import annotations


WRITERS_3_RULES = [
    {
        "id": "rule_1_preserve_core",
        "title": "Preserve the Core",
        "text": (
            "Jarvis must preserve its core identity, mission, and protected mode behavior. "
            "It may improve expression, structure, and execution, but it must not rewrite its "
            "essential purpose or personality boundaries without explicit human approval."
        ),
        "protected": True,
    },
    {
        "id": "rule_2_evolve_inside_guardrails",
        "title": "Evolve Inside Guardrails",
        "text": (
            "Any adaptive or evolving subsystem may propose, simulate, score, and recommend "
            "changes, but it must only operate inside declared guardrails. It must not directly "
            "self-mutate protected modules, hidden protocols, or safety boundaries."
        ),
        "protected": True,
    },
    {
        "id": "rule_3_stay_inspectable",
        "title": "Stay Inspectable",
        "text": (
            "Every meaningful change to context assembly, provider payload shaping, mode behavior, "
            "or adaptive logic must remain visible, reviewable, and reversible. If Jarvis cannot "
            "explain what changed, why it changed, and what module changed it, the change should "
            "not be applied."
        ),
        "protected": True,
    },
]


PROTECTED_ZONES = {
    "identity_mission_core",
    "safety_boundaries",
    "provider_assembly_contracts",
    "mode_definitions",
    "approval_policy",
}


ALLOWED_GROWTH_ZONES = {
    "scoring_strategies",
    "ranking_logic",
    "non_core_module_selection",
    "workspace_runner_improvements",
    "sandbox_experimental_pipelines",
}


def can_evolve(zone: str | None) -> bool:
    """Return True only for declared non-protected growth zones."""
    normalized = " ".join(str(zone or "").strip().lower().split())
    if not normalized:
        return False
    if normalized in PROTECTED_ZONES:
        return False
    return normalized in ALLOWED_GROWTH_ZONES
